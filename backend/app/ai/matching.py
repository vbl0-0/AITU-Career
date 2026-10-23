"""Explainable deterministic matching; semantic inference can only be partial evidence."""
import logging
import hashlib
import json
import re
from collections import Counter
from datetime import date
from functools import lru_cache
from app.core.config import get_settings

LOGGER = logging.getLogger(__name__)
ALGORITHM_VERSION = 'weighted-skills-1.0'
LEVELS = {1: 'Beginner', 2: 'Intermediate', 3: 'Advanced'}


def context_fingerprint(catalog):
    settings = get_settings()
    context = {'catalog': [(s.id, s.name, sorted(a.name for a in s.aliases)) for s in sorted(catalog, key=lambda x: x.id)],
               'semantic': settings.semantic_enabled, 'model': settings.semantic_model,
               'threshold': settings.semantic_threshold, 'version': ALGORITHM_VERSION}
    return hashlib.sha256(json.dumps(context, sort_keys=True).encode()).hexdigest()


def normalize(value):
    return re.sub(r'\s+', ' ', value.strip().casefold())


def extract_skills(text, catalog):
    """Whole-term matching, including aliases; Java does not match JavaScript."""
    found = []
    for skill in catalog:
        terms = [skill.name] + [a.name for a in skill.aliases]
        for term in terms:
            flags = 0 if term in {'Go', 'R', 'C'} else re.IGNORECASE
            if re.search(r'(?<![\w+#])' + re.escape(term) + r'(?![\w+#])', text, flags):
                found.append(skill)
                break
    return found


def competencies(profile, catalog):
    result = {}

    def add(skill, level, source, inferred=False):
        key = skill.id
        if key not in result:
            result[key] = {'skill_id': key, 'name': skill.name, 'level': level, 'sources': [], 'inferred': inferred}
        elif level > result[key]['level'] or not inferred:
            result[key]['level'] = max(level, result[key]['level'])
            result[key]['inferred'] = result[key]['inferred'] and inferred
        if source not in result[key]['sources']:
            result[key]['sources'].append(source)

    for item in profile.skills:
        add(item.skill, item.level, 'Заявленный навык')
    for project in profile.projects:
        for item in project.technologies:
            add(item.skill, 1, f'Проект: {project.name}')
        for skill in extract_skills(project.description, catalog):
            add(skill, 1, f'Описание проекта: {project.name}', True)
    for experience in profile.experience:
        for skill in extract_skills(experience.position + ' ' + experience.description, catalog):
            add(skill, 1, f'Опыт: {experience.company}', True)
    for cert in profile.certificates:
        for skill in extract_skills(cert.name, catalog):
            add(skill, 1, f'Сертификат: {cert.name}', True)
    return list(result.values())


@lru_cache(maxsize=1)
def semantic_model():
    settings = get_settings()
    if not settings.semantic_enabled:
        return None
    try:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer(settings.semantic_model, local_files_only=True)
    except Exception:
        LOGGER.warning('Semantic model unavailable; using keyword fallback', exc_info=True)
        return None


def semantic_candidate(name, available):
    model = semantic_model()
    if model is None or not available:
        return None
    try:
        vectors = model.encode([name] + [c['name'] for c in available], normalize_embeddings=True)
        similarity = vectors[1:] @ vectors[0]
        index = int(similarity.argmax())
        if float(similarity[index]) >= get_settings().semantic_threshold:
            return available[index], round(float(similarity[index]), 4)
    except Exception:
        LOGGER.warning('Semantic inference failed; using keyword fallback', exc_info=True)
    return None


def score_requirements(available, requirements, semantic=False):
    by_id = {c['skill_id']: c for c in available}
    groups = {'matched': [], 'partial': [], 'missing': []}
    earned = total = 0.0
    for requirement in requirements:
        weight = requirement['weight']
        total += weight
        competency = by_id.get(requirement['skill_id'])
        similarity = None
        method = 'canonical'
        if competency is None and semantic:
            candidate = semantic_candidate(requirement['name'], available)
            if candidate:
                competency, similarity = candidate
                method = 'semantic'
        value = 0.0
        if competency:
            value = min(1.0, competency['level'] / requirement['level'])
            if competency.get('inferred') or method == 'semantic':
                value = min(value, 0.5)
        earned += weight * value
        group = 'matched' if value == 1 else 'partial' if value > 0 else 'missing'
        groups[group].append({**requirement, 'contribution': round(value, 4),
                              'user_level': competency['level'] if competency else None,
                              'sources': competency['sources'] if competency else [],
                              'method': method, 'similarity': similarity,
                              'related_skill': competency['name'] if competency and method == 'semantic' else None})
    score = round(100 * earned / total, 1) if total else None
    return {'score': score, **groups, 'weighted_earned': round(earned, 4), 'weighted_total': total}


def analyze(profile, job, catalog):
    available = competencies(profile, catalog)
    requirements = [{'skill_id': s.skill_id, 'name': s.skill.name, 'required': s.required,
                     'level': s.level, 'weight': s.weight} for s in job.skills]
    extracted = False
    if not requirements:
        extracted = True
        requirements = [{'skill_id': s.id, 'name': s.name, 'required': True, 'level': 1, 'weight': 2.0}
                        for s in extract_skills(job.description, catalog)]
    result = score_requirements(available, requirements, get_settings().semantic_enabled)
    gaps = result['missing'] + result['partial']
    if result['score'] is None:
        explanation = 'Недостаточно требований для расчёта. В вакансии нужно указать навыки.'
    elif not gaps:
        explanation = 'Твои компетенции покрывают все перечисленные требования к навыкам. Перед откликом проверь обязанности и ожидания по опыту.'
    else:
        names = ', '.join(s['name'] for s in sorted(gaps, key=lambda x: -x['weight'])[:3])
        explanation = f"Полностью покрыто требований: {len(result['matched'])} из {len(requirements)}. Усиль {names}, чтобы повысить соответствие."
    mode = 'keyword+semantic' if get_settings().semantic_enabled and semantic_model() is not None else 'keyword'
    return {**result, 'job_id': job.id, 'job_title': job.title, 'competencies': available,
            'explanation': explanation, 'algorithm_version': ALGORITHM_VERSION,
            'mode': mode, 'requirements_extracted': extracted,
            'context_fingerprint': context_fingerprint(catalog),
            'profile_revision': profile.revision, 'job_revision': job.revision,
            'formula': '100 × sum(weight × contribution) / sum(weight)',
            'recommendations': [{'skill': s['name'], 'action': f"Закрепи {s['name']} в небольшом проекте и обнови уровень владения в профиле.",
                                 'reason': 'Недостающий навык' if s['contribution'] == 0 else 'Нужно усилить уровень или подтверждение навыка',
                                 'required': s['required']} for s in sorted(gaps, key=lambda x: -x['weight'])[:5]]}


def career_summary(profile, jobs, catalog):
    ranked = [(job, analyze(profile, job, catalog)) for job in jobs]
    ranked.sort(key=lambda pair: (pair[1]['score'] is not None, pair[1]['score'] or 0), reverse=True)
    target = [p for p in ranked if p[0].role_id == profile.desired_role_id] if profile.desired_role_id else ranked
    selected = [p for p in target if p[1]['score'] is not None][:5]
    market = sum(p[1]['score'] for p in selected) / (100 * len(selected)) if selected else 0
    relevant = {s['skill_id'] for _, match in selected
                for group in ('matched', 'partial', 'missing') for s in match[group]}
    project_skills = {t.skill_id for p in profile.projects for t in p.technologies}
    project_component = len(relevant & project_skills) / len(relevant) if relevant else 0
    days = set()
    for exp in profile.experience:
        text = exp.position + ' ' + exp.description
        if any(s.id in relevant for s in extract_skills(text, catalog)):
            start = exp.start_date.toordinal()
            end = min(exp.end_date or date.today(), date.today()).toordinal()
            days.update(range(max(start, end - 3650), end + 1))
    experience_component = min(1, len(days) / 180)
    related_certs = sum(any(s.id in relevant for s in extract_skills(c.name, catalog)) for c in profile.certificates)
    certificate_component = min(1, related_certs / 2)
    education_component = max((sum(bool(x) for x in (e.university, e.degree, e.program, e.graduation_year)) / 4
                               for e in profile.education), default=0)
    settings = get_settings()
    values = {'market': market, 'projects': project_component, 'experience': experience_component,
              'certificates': certificate_component, 'education': education_component}
    weights = {k: getattr(settings, f'readiness_{k}_weight') for k in values}
    denominator = sum(weights.values())
    contributions = {k: round(100 * values[k] * weights[k] / denominator, 2) if denominator else 0 for k in values}
    gaps = Counter()
    for _, match in selected:
        for s in match['missing'] + match['partial']:
            gaps[s['name']] += s['weight'] * (1 - s['contribution'])
    skill_gaps = [{'skill': name, 'priority': round(priority, 2),
                  'action': f'Создай проект с {name} и пересчитай соответствие выбранным вакансиям.'}
                 for name, priority in gaps.most_common(6)]
    role_scores = {}
    for job, result in ranked:
        if result['score'] is not None:
            role_scores.setdefault(job.role.name, []).append(result['score'])
    career_directions = sorted([{'role': role, 'score': round(sum(sorted(scores, reverse=True)[:3]) / min(3, len(scores)), 1)}
                                for role, scores in role_scores.items()], key=lambda x: -x['score'])[:5]
    recommendations = target
    return {'readiness': round(sum(contributions.values()), 1), 'readiness_components': values,
            'readiness_weights': weights, 'readiness_contributions': contributions,
            'market_sample_size': len(selected), 'scope': 'Seed/demo vacancies' if jobs and all(j.is_demo for j in jobs) else 'Current platform vacancies',
            'competency_count': len(competencies(profile, catalog)),
            'top_skills': sorted(competencies(profile, catalog), key=lambda s: -s['level'])[:8],
            'skill_gaps': skill_gaps, 'skill_gap_count': len(gaps), 'career_directions': career_directions,
            'desired_role': profile.desired_role.name if profile.desired_role else None,
            'recommended_job_count': sum(m['score'] is not None and m['score'] > 0 for _, m in recommendations),
            'recommended_jobs': [{'id': j.id, 'title': j.title, 'company': j.company, 'location': j.location,
                                  'employment_type': j.employment_type,
                                  'skills': [{'name': s['name'], 'required': s['required']}
                                             for group in ('matched', 'partial', 'missing') for s in m[group]],
                                  'score': m['score'], 'is_demo': j.is_demo} for j, m in recommendations[:6]],
            'profile_improvements': (["Выбери карьерное направление."] if not profile.desired_role_id else [])
                                  + (["Добавь образование AITU."] if not profile.education else [])
                                  + (["Добавь навыки с текущими уровнями."] if not profile.skills else [])
                                  + (["Добавь проект и его технологии."] if not profile.projects else []),
            'explanation': 'Readiness combines your top five target-role matches, relevant project skill coverage, up to 180 non-overlapping experience days, up to two relevant certificates, and education completeness.'}
