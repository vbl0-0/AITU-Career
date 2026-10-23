"""Bounded, explicit imports using the official HeadHunter API. No HTML scraping."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from html.parser import HTMLParser
import json
from urllib.parse import urlparse
import httpx
from sqlalchemy import select
from app.ai.matching import extract_skills
from app.core.config import get_settings
from app.database.session import SessionLocal
from app.models import CareerRole, Job, JobCategory, JobSkill, Skill
from app.repositories.common import commit, require
from app.schemas.inputs import HHImportInput, HHSyncInput


class HHError(Exception):
    pass


class DescriptionParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.ignored = 0

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self.ignored += 1
        if tag in ('p', 'br', 'li', 'div'):
            self.parts.append('\n')

    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self.ignored = max(0, self.ignored - 1)
        if tag in ('p', 'li', 'div'):
            self.parts.append('\n')

    def handle_data(self, data):
        if not self.ignored:
            self.parts.append(data)


class HHClient:
    def __init__(self, *, transport=None):
        settings = get_settings()
        headers = {'User-Agent': settings.hh_user_agent, 'HH-User-Agent': settings.hh_user_agent, 'Accept': 'application/json'}
        if settings.hh_access_token:
            headers['Authorization'] = 'Bearer ' + settings.hh_access_token
        self.http = httpx.Client(base_url='https://api.hh.ru', headers=headers, timeout=settings.hh_timeout_seconds,
                                 follow_redirects=False, transport=transport)

    def close(self):
        self.http.close()

    def request(self, path, params=None, allow_missing=False):
        try:
            response = self.http.get(path, params=params)
        except httpx.HTTPError:
            raise HHError('errors.hhConnection') from None
        if allow_missing and response.status_code in (404, 410):
            return None
        if response.status_code in (401, 403):
            raise HHError('errors.hhAccess')
        if response.status_code == 429:
            raise HHError('errors.hhRateLimit')
        if not response.is_success:
            raise HHError('errors.hhConnection')
        try:
            data = response.json()
        except ValueError:
            raise HHError('errors.hhResponse') from None
        if not isinstance(data, dict):
            raise HHError('errors.hhResponse')
        return data

    def search(self, options):
        params = {'host': 'hh.kz', 'area': options.area_id, 'text': options.text,
                  'per_page': options.limit, 'page': 0, 'order_by': 'publication_time'}
        if options.experience:
            params['experience'] = options.experience
        data = self.request('/vacancies', params)
        items = data.get('items')
        if not isinstance(items, list):
            raise HHError('errors.hhResponse')
        identifiers = []
        for item in items[:options.limit]:
            identifier = item.get('id') if isinstance(item, dict) else None
            if not isinstance(identifier, str) or not identifier.isascii() or not identifier.isdigit() or len(identifier) > 80:
                raise HHError('errors.hhResponse')
            if identifier not in identifiers:
                identifiers.append(identifier)
        return identifiers

    def vacancy(self, identifier):
        if not identifier.isascii() or not identifier.isdigit() or len(identifier) > 80:
            raise HHError('errors.hhResponse')
        data = self.request('/vacancies/' + identifier, {'host': 'hh.kz'}, allow_missing=True)
        if data is not None and str(data.get('id')) != identifier:
            raise HHError('errors.hhResponse')
        return data


def normalize(data, role_id, category_id, catalog):
    parser = DescriptionParser()
    parser.feed(data.get('description') or '')
    description = '\n'.join(line.strip() for line in ''.join(parser.parts).splitlines() if line.strip())[:15000]
    title, company = data.get('name'), (data.get('employer') or {}).get('name')
    location = (data.get('area') or {}).get('name')
    if not all(isinstance(value, str) and value.strip() for value in (title, company, location, description)):
        raise ValueError('Incomplete vacancy')
    source_url = data.get('alternate_url')
    parsed = urlparse(source_url or '')
    if len(source_url or '') > 500 or parsed.scheme != 'https' or parsed.username or parsed.password or not parsed.hostname or not any(
            parsed.hostname == host or parsed.hostname.endswith('.' + host) for host in ('hh.kz', 'hh.ru')):
        raise ValueError('Invalid source URL')
    salary = data.get('salary_range') or data.get('salary') or {}
    def amount(value):
        return int(value) if isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0 and value == int(value) else None
    minimum, maximum = amount(salary.get('from')), amount(salary.get('to'))
    if minimum is not None and maximum is not None and minimum > maximum:
        raise ValueError('Invalid salary range')
    currency = salary.get('currency')
    if not currency:
        minimum = maximum = None
        currency = 'KZT'
    if not isinstance(currency, str) or len(currency) != 3:
        raise ValueError('Invalid currency')
    employment = data.get('employment') or {}
    employment_type = {'full': 'Full-time', 'part': 'Part-time', 'project': 'Freelance', 'probation': 'Internship'}.get(employment.get('id'), employment.get('name') or '')
    published = data.get('published_at')
    published_at = datetime.fromisoformat(published) if published else None
    if published_at and published_at.tzinfo is None:
        published_at = published_at.replace(tzinfo=timezone.utc)
    keywords = [item.get('name', '') for item in data.get('key_skills', []) if isinstance(item, dict)]
    skills = extract_skills(' '.join(keywords) if keywords else description, catalog)
    fields = {'title': title.strip()[:150], 'company': company.strip()[:150], 'location': location.strip()[:150],
              'description': description, 'employment_type': employment_type[:30],
              'experience_level': ((data.get('experience') or {}).get('name') or '')[:50],
              'salary_min': minimum, 'salary_max': maximum, 'currency': currency,
              'role_id': role_id, 'category_id': category_id, 'source_url': source_url[:500],
              'source_published_at': published_at, 'is_active': not bool(data.get('archived', False)), 'is_demo': False}
    return fields, sorted(skill.id for skill in skills)


def synchronize(db, options, *, refresh=False, client=None):
    """Fetch/validate before writing; never close jobs merely absent from a limited search."""
    if options.role_id:
        require(db, CareerRole, options.role_id)
    if not refresh:
        require(db, JobCategory, options.category_id)
    owned_client = client is None
    client = client or HHClient()
    try:
        if refresh:
            query = select(Job).where(Job.source == 'hh', Job.external_id.is_not(None))
            if options.role_id:
                query = query.where(Job.role_id == options.role_id)
            existing = list(db.scalars(query.order_by(Job.last_synced_at.asc().nullsfirst(), Job.id).limit(options.limit)))
            identifiers = [job.external_id for job in existing]
        else:
            identifiers = client.search(options)
            existing = list(db.scalars(select(Job).where(Job.source == 'hh', Job.external_id.in_(identifiers))))
        by_external = {job.external_id: job for job in existing}
        # A bounded network batch; database access stays in the calling thread.
        with ThreadPoolExecutor(max_workers=4) as executor:
            details = list(executor.map(client.vacancy, identifiers))
        catalog = list(db.scalars(select(Skill)))
        changes = []
        result = {'created': 0, 'updated': 0, 'unchanged': 0, 'archived': 0, 'skipped': 0}
        for identifier, data in zip(identifiers, details):
            job = by_external.get(identifier)
            if data is None or data.get('archived') is True:
                changes.append((job, None, []))
                if job is None:
                    result['skipped'] += 1
                continue
            try:
                fields, skills = normalize(data, job.role_id if refresh else options.role_id,
                                           job.category_id if refresh else options.category_id, catalog)
            except (ValueError, TypeError, AttributeError):
                result['skipped'] += 1
                continue
            changes.append((job, (identifier, fields), skills))
        checked_at = datetime.now(timezone.utc)
        for job, payload, skills in changes:
            if payload is None:
                if job is not None:
                    if job.is_active:
                        job.is_active = False
                        job.revision += 1
                        result['archived'] += 1
                    else:
                        result['unchanged'] += 1
                    job.last_synced_at = checked_at
                continue
            identifier, fields = payload
            if job is None:
                job = Job(source='hh', external_id=identifier, **fields)
                db.add(job)
                changed = True
                result['created'] += 1
            else:
                current_skills = sorted((item.skill_id, item.required, item.level, item.weight) for item in job.skills)
                changed = any(getattr(job, key) != value for key, value in fields.items()) or current_skills != [(skill, True, 1, 2) for skill in skills]
                result['updated' if changed else 'unchanged'] += 1
                if changed:
                    for key, value in fields.items():
                        setattr(job, key, value)
                    job.revision += 1
            if changed:
                job.skills.clear()
                db.flush()
                job.skills = [JobSkill(skill_id=skill, required=True, level=1, weight=2) for skill in skills]
            job.last_synced_at = checked_at
        commit(db)
        return result
    finally:
        if owned_client:
            client.close()


def main():
    parser = argparse.ArgumentParser(description='Import or refresh vacancies through the official HeadHunter API.')
    parser.add_argument('--sync', action='store_true', help='Refresh existing imported vacancies instead of searching')
    parser.add_argument('--query', help='Search terms for import')
    parser.add_argument('--role-id', type=int)
    parser.add_argument('--category-id', type=int)
    parser.add_argument('--area-id', default='40')
    parser.add_argument('--limit', type=int, default=10)
    args = parser.parse_args()
    from pydantic import ValidationError
    from fastapi import HTTPException
    try:
        options = HHSyncInput(role_id=args.role_id, limit=args.limit) if args.sync else HHImportInput(
            text=args.query or '', role_id=args.role_id or 0, category_id=args.category_id or 0, area_id=args.area_id, limit=args.limit)
        with SessionLocal() as db:
            result = synchronize(db, options, refresh=args.sync)
        print(json.dumps(result))
    except HHError as error:
        parser.exit(1, str(error) + ': HeadHunter request failed; no import changes saved.\n')
    except (ValidationError, HTTPException):
        parser.exit(1, 'Invalid import options or unknown role/category.\n')


if __name__ == '__main__':
    main()
