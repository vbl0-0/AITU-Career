"""No live HH calls: exercise the real client with HTTPX transport fixtures and migrated PostgreSQL."""
import httpx
import pytest


def vacancy(identifier='900001', **changes):
    return {'id': identifier, 'name': 'Test HH Python Developer', 'employer': {'name': 'Test HH Employer'},
            'area': {'name': 'Astana'}, 'description': '<p>Build Python services.</p><ul><li>FastAPI</li></ul><script>ignore()</script>',
            'key_skills': [{'name': 'Python'}, {'name': 'FastAPI'}], 'archived': False,
            'employment': {'id': 'full', 'name': 'Full-time'}, 'experience': {'id': 'noExperience', 'name': 'No experience'},
            'salary': {'from': 300000, 'to': None, 'currency': 'KZT'},
            'alternate_url': f'https://hh.kz/vacancy/{identifier}', 'published_at': '2026-10-19T09:00:00+05:00', **changes}


@pytest.fixture
def provider(monkeypatch):
    from app.services import hh_import
    state = {'records': {'900001': vacancy()}, 'search_ids': ['900001'], 'status': 200, 'calls': []}
    def handler(request):
        state['calls'].append((request.url.path, dict(request.url.params)))
        if state['status'] != 200:
            return httpx.Response(state['status'], json={'errors': [{'type': 'forbidden'}]})
        if request.url.path == '/vacancies':
            return httpx.Response(200, json={'items': [{'id': identifier} for identifier in state['search_ids']]})
        record = state['records'].get(request.url.path.split('/')[-1])
        if isinstance(record, int):
            return httpx.Response(record, json={})
        return httpx.Response(200, json=record) if record else httpx.Response(404, json={})
    client_class = hh_import.HHClient
    monkeypatch.setattr(hh_import, 'HHClient', lambda: client_class(transport=httpx.MockTransport(handler)))
    return state


def options(client):
    roles = client.get('/api/catalog/career-roles').json()
    category = client.get('/api/catalog/job-categories').json()[0]
    return {'text': 'Python', 'role_id': next(role['id'] for role in roles if role['name'] == 'Backend Developer'),
            'category_id': category['id'], 'limit': 10}


def test_import_is_idempotent_preserves_provenance_and_invalidates_changed_matches(admin, provider):
    body = options(admin)
    first = admin.post('/api/admin/jobs/import/hh', json=body)
    assert first.status_code == 200, first.text
    assert first.json()['created'] == 1
    job = next(job for job in admin.get('/api/admin/jobs').json() if job['source'] == 'hh')
    assert job['external_id'] == '900001' and not job['is_demo'] and job['is_active']
    assert job['source_url'] == 'https://hh.kz/vacancy/900001'
    assert '<p>' not in job['description'] and 'ignore()' not in job['description']
    assert {skill['name'] for skill in job['skills']} == {'Python', 'FastAPI'}
    assert job['salary_min'] == 300000 and job['salary_max'] is None
    assert job['source_published_at'] and job['last_synced_at']
    old_match = admin.post(f"/api/jobs/{job['id']}/match").json()
    repeated = admin.post('/api/admin/jobs/import/hh', json=body).json()
    assert repeated['created'] == repeated['updated'] == 0
    assert repeated['unchanged'] == 1
    assert len(admin.get('/api/admin/jobs').json()) == 31
    assert not admin.get(f"/api/matches/{old_match['id']}").json()['stale']
    provider['records']['900001']['salary']['from'] = 350000
    assert admin.post('/api/admin/jobs/import/hh', json=body).json()['updated'] == 1
    assert admin.get(f"/api/matches/{old_match['id']}").json()['stale']
    search_params = next(params for path, params in provider['calls'] if path == '/vacancies')
    assert search_params['area'] == '40' and search_params['host'] == 'hh.kz'
    assert search_params['experience'] == 'noExperience'


@pytest.mark.parametrize('status, key', [(403, 'errors.hhAccess'), (401, 'errors.hhAccess'),
                                        (429, 'errors.hhRateLimit'), (500, 'errors.hhConnection')])
def test_provider_failure_is_explicit_and_does_not_change_database(admin, provider, status, key):
    provider['status'] = status
    response = admin.post('/api/admin/jobs/import/hh', json=options(admin))
    assert response.status_code == 502
    assert response.json()['detail'] == key
    assert len(admin.get('/api/admin/jobs').json()) == 30


def test_imported_vacancy_can_be_edited_without_inventing_experience_or_employment(admin, provider):
    admin.post('/api/admin/jobs/import/hh', json=options(admin))
    job = next(job for job in admin.get('/api/admin/jobs').json() if job['source'] == 'hh')
    fields = ('title', 'company', 'location', 'description', 'employment_type', 'experience_level',
              'salary_min', 'salary_max', 'currency', 'role_id', 'category_id')
    body = {key: job[key] for key in fields}
    body['skills'] = [{key: skill[key] for key in ('skill_id', 'required', 'level', 'weight')} for skill in job['skills']]
    for experience, employment in [('No experience', 'Flexible schedule'), ('', '')]:
        body.update(experience_level=experience, employment_type=employment)
        result = admin.put(f"/api/admin/jobs/{job['id']}", json=body)
        assert result.status_code == 200, result.text
        assert result.json()['experience_level'] == experience
        assert result.json()['employment_type'] == employment
        assert result.json()['source'] == 'hh' and result.json()['external_id'] == '900001'


def test_graduate_cannot_import_or_refresh(graduate, provider):
    assert graduate.post('/api/admin/jobs/import/hh', json=options(graduate)).status_code == 403
    assert graduate.post('/api/admin/jobs/sync/hh', json={}).status_code == 403
    assert provider['calls'] == []


@pytest.mark.parametrize('unavailable', [None, 404, 410, {'archived': True}])
def test_refresh_hides_confirmed_unavailable_jobs_and_preserves_saved_links(admin, provider, unavailable):
    assert admin.post('/api/admin/jobs/import/hh', json=options(admin)).status_code == 200
    job = next(job for job in admin.get('/api/admin/jobs').json() if job['source'] == 'hh')
    admin.post(f"/api/saved-jobs/{job['id']}")
    provider['records']['900001'] = vacancy(archived=True) if isinstance(unavailable, dict) else unavailable
    refreshed = admin.post('/api/admin/jobs/sync/hh', json={})
    assert refreshed.status_code == 200 and refreshed.json()['archived'] == 1
    assert not admin.get(f"/api/jobs/{job['id']}").json()['is_active']
    assert admin.get('/api/jobs?q=Test%20HH').json()['items'] == []
    assert not next(saved for saved in admin.get('/api/saved-jobs').json() if saved['id'] == job['id'])['is_active']
    assert admin.post(f"/api/jobs/{job['id']}/match").status_code == 409
    provider['records']['900001'] = vacancy()
    assert admin.post('/api/admin/jobs/sync/hh', json={}).json()['updated'] == 1
    assert admin.get(f"/api/jobs/{job['id']}").json()['is_active']
    assert len(admin.get('/api/admin/jobs').json()) == 31


def test_limited_search_never_archives_a_job_missing_from_its_results(admin, provider):
    body = options(admin)
    admin.post('/api/admin/jobs/import/hh', json=body)
    provider['search_ids'] = []
    assert admin.post('/api/admin/jobs/import/hh', json=body).json()['archived'] == 0
    assert next(job for job in admin.get('/api/admin/jobs').json() if job['source'] == 'hh')['is_active']


def test_detail_request_failure_does_not_save_half_an_import(admin, provider):
    provider['search_ids'] = ['900001', '900002']
    provider['records']['900002'] = 403
    response = admin.post('/api/admin/jobs/import/hh', json=options(admin))
    assert response.status_code == 502
    assert len(admin.get('/api/admin/jobs').json()) == 30


def test_malformed_source_url_is_skipped_without_fabricated_vacancies(admin, provider):
    provider['records']['900001']['alternate_url'] = 'javascript:alert(1)'
    result = admin.post('/api/admin/jobs/import/hh', json=options(admin)).json()
    assert result['created'] == 0 and result['skipped'] == 1
    assert len(admin.get('/api/admin/jobs').json()) == 30


def test_unknown_salary_currency_is_not_presented_as_kzt(admin, provider):
    provider['records']['900001']['salary'].pop('currency')
    assert admin.post('/api/admin/jobs/import/hh', json=options(admin)).json()['created'] == 1
    job = next(job for job in admin.get('/api/admin/jobs').json() if job['source'] == 'hh')
    assert job['salary_min'] is None and job['salary_max'] is None


def test_import_client_rejects_unexpected_payload_and_transmits_token_only_in_headers(monkeypatch):
    from app.core.config import get_settings
    from app.schemas.inputs import HHImportInput
    from app.services.hh_import import HHClient, HHError
    settings = get_settings()
    monkeypatch.setattr(settings, 'hh_access_token', 'test-secret-token')
    def handler(request):
        assert request.headers['Authorization'] == 'Bearer test-secret-token'
        assert 'test-secret-token' not in str(request.url)
        return httpx.Response(200, json=['unexpected payload'])
    client = HHClient(transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(HHError, match='errors.hhResponse'):
            client.search(HHImportInput(text='Python', role_id=1, category_id=1))
    finally:
        client.close()
