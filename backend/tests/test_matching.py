from types import SimpleNamespace as N
import pytest
from datetime import date, timedelta
from app.ai.matching import career_summary, competencies, extract_skills, score_requirements


def competency(identifier, name, level=2, inferred=False):
    return {'skill_id': identifier, 'name': name, 'level': level, 'sources': ['Declared skill'], 'inferred': inferred}


def requirement(identifier, name, level=1, weight=2, required=True):
    return {'skill_id': identifier, 'name': name, 'level': level, 'weight': weight, 'required': required}


def test_four_of_five_is_eighty_percent():
    names = ['Python', 'FastAPI', 'PostgreSQL', 'Docker', 'Git']
    result = score_requirements([competency(i, name) for i, name in enumerate(names) if name != 'FastAPI'],
                                [requirement(i, name) for i, name in enumerate(names)])
    assert result['score'] == 80.0
    assert [s['name'] for s in result['missing']] == ['FastAPI']
    assert len(result['matched']) == 4


def test_partial_proficiency_and_preferred_weights():
    result = score_requirements([competency(1, 'Python', 1)],
                                [requirement(1, 'Python', 2, 2), requirement(2, 'Docker', 1, 1, False)])
    assert result['score'] == 33.3
    assert result['partial'][0]['contribution'] == .5
    assert result['weighted_total'] == 3


@pytest.mark.parametrize('available, expected', [([], 0), ([competency(1, 'Python')], 100)])
def test_score_extremes(available, expected):
    assert score_requirements(available, [requirement(1, 'Python')])['score'] == expected


def test_absent_requirements_have_no_score():
    assert score_requirements([competency(1, 'Python')], [])['score'] is None


def test_text_evidence_cannot_be_a_full_match():
    result = score_requirements([competency(1, 'Python', 1, True)], [requirement(1, 'Python')])
    assert result['score'] == 50
    assert not result['matched']


def test_aliases_and_word_boundaries():
    catalog = [N(id=1, name='JavaScript', aliases=[N(name='js programming')]), N(id=2, name='Java', aliases=[]),
               N(id=3, name='Go', aliases=[]), N(id=4, name='C++', aliases=[]), N(id=5, name='C#', aliases=[])]
    assert [s.id for s in extract_skills('JS Programming and JavaScript; ready to go.', catalog)] == [1]
    assert [s.id for s in extract_skills('Go, C++, C# and Java.', catalog)] == [2, 3, 4, 5]


def test_competencies_keep_strongest_level_and_sources():
    python = N(id=1, name='Python', aliases=[])
    profile = N(skills=[N(skill=python, level=3)], projects=[N(name='API', technologies=[N(skill=python)], description='Python API')],
                experience=[], certificates=[])
    result = competencies(profile, [python])
    assert len(result) == 1
    assert result[0]['level'] == 3
    assert not result[0]['inferred']
    assert len(result[0]['sources']) == 3


def test_semantic_evidence_is_partial(monkeypatch):
    monkeypatch.setattr('app.ai.matching.semantic_candidate', lambda name, available: (available[0], .92))
    result = score_requirements([competency(1, 'JS Development', 3)], [requirement(2, 'JavaScript', 1)], semantic=True)
    assert result['score'] == 50
    assert result['partial'][0]['related_skill'] == 'JS Development'


def test_semantic_unavailable_uses_keyword_fallback(monkeypatch):
    monkeypatch.setattr('app.ai.matching.semantic_model', lambda: None)
    result = score_requirements([competency(1, 'Python')], [requirement(1, 'Python'), requirement(2, 'Docker')], semantic=True)
    assert result['score'] == 50


@pytest.fixture
def summary_data():
    python = N(id=1, name='Python', aliases=[])
    profile = N(skills=[N(skill=python, level=2)],
                projects=[N(name='API', description='', technologies=[N(skill_id=1, skill=python)])],
                experience=[N(company='Lab', position='Python intern', description='',
                              start_date=date.today() - timedelta(days=179), end_date=date.today())],
                certificates=[N(name='Python Fundamentals')],
                education=[N(university='AITU', degree='Bachelor', program='SE', graduation_year=2026)],
                desired_role_id=1, desired_role=N(name='Backend Developer'), revision=1)
    job = N(id=1, role_id=1, role=N(name='Backend Developer'), title='Python Developer',
            company='Example', location='Astana', employment_type='Full-time', is_demo=False,
            description='Python', revision=1, skills=[])
    return profile, job, [python]


def test_text_and_structured_requirements_use_the_same_readiness_evidence(summary_data):
    profile, job, catalog = summary_data
    text = career_summary(profile, [job], catalog)
    job.skills = [N(skill_id=1, skill=catalog[0], required=True, level=1, weight=2)]
    structured = career_summary(profile, [job], catalog)
    assert text['recommended_jobs'][0]['score'] == structured['recommended_jobs'][0]['score'] == 100
    assert text['readiness_components'] == structured['readiness_components']
    assert text['readiness_components'] == {'market': 1, 'projects': 1, 'experience': 1,
                                           'certificates': .5, 'education': 1}
    assert text['readiness'] == structured['readiness']


def test_missing_target_role_does_not_silently_recommend_other_roles(summary_data):
    profile, job, catalog = summary_data
    profile.desired_role_id = 2
    profile.desired_role = N(name='Frontend Developer')
    result = career_summary(profile, [job], catalog)
    assert result['recommended_jobs'] == []
    assert result['recommended_job_count'] == 0
    assert result['market_sample_size'] == 0
    assert result['skill_gaps'] == []
    assert result['career_directions'][0]['role'] == 'Backend Developer'


def test_no_target_role_still_uses_available_vacancies(summary_data):
    profile, job, catalog = summary_data
    profile.desired_role_id = None
    profile.desired_role = None
    result = career_summary(profile, [job], catalog)
    assert result['recommended_job_count'] == result['market_sample_size'] == 1


def test_readiness_does_not_double_count_overlapping_experience(summary_data):
    profile, job, catalog = summary_data
    profile.experience[0].start_date = date.today() - timedelta(days=29)
    profile.experience.append(N(**vars(profile.experience[0])))
    result = career_summary(profile, [job], catalog)
    assert result['readiness_components']['experience'] == pytest.approx(30 / 180)


def test_unrelated_projects_experience_and_certificates_do_not_add_readiness(summary_data):
    profile, job, catalog = summary_data
    profile.projects[0].technologies = []
    profile.experience[0].position = 'Unrelated internship'
    profile.certificates[0].name = 'Unrelated course'
    result = career_summary(profile, [job], catalog)
    assert result['readiness_components']['market'] == 1
    assert all(result['readiness_components'][key] == 0 for key in ('projects', 'experience', 'certificates'))


def test_inferred_vacancy_requirements_still_produce_prioritized_gaps(summary_data):
    profile, job, catalog = summary_data
    catalog.append(N(id=2, name='Docker', aliases=[]))
    job.description = 'Python and Docker'
    result = career_summary(profile, [job], catalog)
    assert result['recommended_jobs'][0]['score'] == 50
    assert result['skill_gaps'][0]['skill'] == 'Docker'
    assert result['readiness_components']['projects'] == .5
