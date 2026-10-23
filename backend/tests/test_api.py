import os
from datetime import date, timedelta
from sqlalchemy import func, select


def register(client, email='new.graduate@aitu.edu.kz'):
    response = client.post('/api/auth/register', json={'email': email, 'password': 'Test-only-password-42!', 'name': 'New Graduate'})
    assert response.status_code == 201, response.text
    client.headers['Authorization'] = 'Bearer ' + response.json()['access_token']
    return response


def test_registration_login_and_password_hash(client, seeded):
    from app.models import User
    register(client)
    assert client.get('/api/profile').json()['name'] == 'New Graduate'
    duplicate = client.post('/api/auth/register', json={'email': 'NEW.GRADUATE@aitu.edu.kz', 'password': 'Test-only-password-42!', 'name': 'Other User'})
    assert duplicate.status_code == 409
    assert client.post('/api/auth/login', json={'email': 'new.graduate@aitu.edu.kz', 'password': 'wrong'}).status_code == 401
    assert client.post('/api/auth/login', json={'email': 'new.graduate@aitu.edu.kz', 'password': 'Test-only-password-42!'}).status_code == 200
    with seeded() as db:
        user = db.scalar(select(User).where(User.email == 'new.graduate@aitu.edu.kz'))
        assert user.password_hash.startswith('$argon2id$')
        assert 'Test-only-password-42!' not in user.password_hash


def test_registration_cannot_grant_admin(client):
    assert client.post('/api/auth/register', json={'email': 'attacker@aitu.edu.kz', 'password': 'Test-only-password-42!', 'name': 'Attacker', 'role': 'admin'}).status_code == 422
    assert client.post('/api/auth/register', json={'email': 'short@aitu.edu.kz', 'password': 'short', 'name': 'Short'}).status_code == 422


def test_protected_routes_and_jwt_tampering(client):
    assert client.get('/api/profile').status_code == 401
    result = register(client)
    client.headers['Authorization'] = 'Bearer ' + result.json()['access_token'][:-8] + 'tampered'
    assert client.get('/api/profile').status_code == 401


def test_refresh_rotation_logout_and_origin_check(graduate):
    old_refresh = graduate.cookies.get('aitu_refresh')
    assert graduate.post('/api/auth/refresh', headers={'Origin': 'https://untrusted.invalid'}).status_code == 403
    assert graduate.post('/api/auth/refresh').status_code == 200
    new_refresh = graduate.cookies.get('aitu_refresh')
    assert old_refresh != new_refresh
    assert graduate.post('/api/auth/refresh', headers={'Cookie': f'aitu_refresh={old_refresh}'}).status_code == 401
    assert graduate.post('/api/auth/logout').status_code == 204
    assert graduate.get('/api/profile').status_code == 401
    assert graduate.post('/api/auth/refresh').status_code == 401


def test_profile_and_education_crud(graduate):
    role = graduate.get('/api/catalog/career-roles').json()[0]
    body = {'name': 'Updated Name', 'location': 'Astana', 'desired_role_id': role['id'], 'bio': 'AITU student'}
    assert graduate.put('/api/profile', json=body).status_code == 200
    assert graduate.get('/api/profile').json()['desired_role_id'] == role['id']
    created = graduate.post('/api/education', json={'program': 'Computer Science', 'graduation_year': 2027})
    assert created.status_code == 201
    identifier = created.json()['id']
    assert graduate.put(f'/api/education/{identifier}', json={'program': 'Software Engineering', 'graduation_year': 2028}).status_code == 200
    assert graduate.delete(f'/api/education/{identifier}').status_code == 204


def test_skills_crud_and_uniqueness(graduate):
    catalog = graduate.get('/api/catalog/skills').json()
    skill = next(s for s in catalog if s['name'] == 'FastAPI')
    created = graduate.post('/api/skills', json={'skill_id': skill['id'], 'level': 1})
    assert created.status_code == 201
    identifier = created.json()['id']
    assert graduate.post('/api/skills', json={'skill_id': skill['id'], 'level': 2}).status_code == 409
    assert graduate.put(f'/api/skills/{identifier}', json={'skill_id': skill['id'], 'level': 3}).json()['level'] == 3
    assert graduate.post('/api/skills', json={'skill_id': skill['id'], 'level': 4}).status_code == 422
    assert graduate.post('/api/skills', json={'skill_id': 9999999, 'level': 1}).status_code == 422
    assert graduate.delete(f'/api/skills/{identifier}').status_code == 204


def test_projects_certificates_and_experience_crud(graduate):
    skill_id = graduate.get('/api/catalog/skills').json()[0]['id']
    body = {'name': 'University API', 'description': 'Python API coursework', 'github_url': 'https://github.com/example/project', 'skill_ids': [skill_id]}
    response = graduate.post('/api/projects', json=body)
    assert response.status_code == 201, response.text
    identifier = response.json()['id']
    assert response.json()['skill_ids'] == [skill_id]
    body['name'] = 'Updated API'
    assert graduate.put(f'/api/projects/{identifier}', json=body).json()['name'] == 'Updated API'
    assert graduate.post('/api/projects', json={**body, 'github_url': 'javascript:alert(1)'}).status_code == 422
    assert graduate.delete(f'/api/projects/{identifier}').status_code == 204
    cert = {'name': 'Python Fundamentals', 'issuer': 'AITU Demo', 'issued_date': str(date.today())}
    response = graduate.post('/api/certificates', json=cert)
    assert response.status_code == 201
    identifier = response.json()['id']
    assert graduate.put(f'/api/certificates/{identifier}', json={**cert, 'name': 'Python Advanced'}).status_code == 200
    assert graduate.delete(f'/api/certificates/{identifier}').status_code == 204
    exp = {'company': 'Example Lab', 'position': 'Python Intern', 'start_date': str(date.today() - timedelta(days=30)), 'end_date': None}
    response = graduate.post('/api/experience', json=exp)
    assert response.status_code == 201
    identifier = response.json()['id']
    assert graduate.put(f'/api/experience/{identifier}', json={**exp, 'description': 'Practiced Python and SQL'}).status_code == 200
    assert graduate.post('/api/experience', json={**exp, 'end_date': str(date.today() - timedelta(days=60))}).status_code == 422
    assert graduate.delete(f'/api/experience/{identifier}').status_code == 204


def test_other_users_items_are_private(graduate):
    project = graduate.get('/api/projects').json()[0]
    match = graduate.post('/api/jobs/' + str(graduate.get('/api/jobs').json()['items'][0]['id']) + '/match').json()
    register(graduate, 'second.graduate@aitu.edu.kz')
    assert graduate.delete('/api/projects/' + str(project['id'])).status_code == 404
    assert graduate.get('/api/matches/' + str(match['id'])).status_code == 404
    assert graduate.get('/api/projects').json() == []


def test_jobs_filters_pagination_and_saving(graduate):
    response = graduate.get('/api/jobs?limit=7')
    assert response.status_code == 200, response.text
    assert response.json()['total'] == 30
    assert len(response.json()['items']) == 7
    job = response.json()['items'][0]
    assert graduate.get('/api/jobs?q=Python').json()['total'] >= 1
    assert graduate.get('/api/jobs?q=%25').json()['total'] == 0
    assert all(j['location'] == 'Remote' for j in graduate.get('/api/jobs?location=Remote').json()['items'])
    identifier = job['id']
    assert graduate.get(f'/api/jobs/{identifier}').status_code == 200
    assert graduate.post(f'/api/saved-jobs/{identifier}').status_code == 201
    assert graduate.post(f'/api/saved-jobs/{identifier}').status_code == 201
    assert len(graduate.get('/api/saved-jobs').json()) == 1
    assert graduate.delete(f'/api/saved-jobs/{identifier}').status_code == 204
    assert graduate.get('/api/saved-jobs').json() == []


def test_match_changes_with_skills_and_old_analysis_is_stale(graduate):
    job = next(j for j in graduate.get('/api/jobs?limit=100').json()['items'] if j['title'] == 'Junior Python Backend Developer')
    first = graduate.post(f"/api/jobs/{job['id']}/match").json()
    assert 'FastAPI' in [s['name'] for s in first['missing']]
    skill = next(s for s in graduate.get('/api/catalog/skills').json() if s['name'] == 'FastAPI')
    assert graduate.post('/api/skills', json={'skill_id': skill['id'], 'level': 2}).status_code == 201
    second = graduate.post(f"/api/jobs/{job['id']}/match").json()
    assert second['score'] > first['score']
    assert not any(s['name'] == 'FastAPI' for s in second['missing'])
    assert graduate.get(f"/api/matches/{first['id']}").json()['stale']
    assert not graduate.get(f"/api/matches/{second['id']}").json()['stale']


def test_dashboard_readiness_and_recommendations(graduate):
    result = graduate.get('/api/recommendations')
    assert result.status_code == 200, result.text
    body = result.json()
    assert 0 <= body['readiness'] <= 100
    assert abs(body['readiness'] - sum(body['readiness_contributions'].values())) <= .1
    assert body['market_sample_size'] > 0
    assert body['recommended_jobs']
    assert body['skill_gaps']
    assert body['career_directions']
    assert graduate.get('/api/dashboard').json()['readiness'] == body['readiness']
    profile = graduate.get('/api/profile').json()
    jobs = graduate.get(f"/api/jobs?limit=100&role_id={profile['desired_role_id']}").json()['items']
    assert body['desired_role'] == profile['desired_role']
    assert body['recommended_job_count'] == sum(j['score'] is not None and j['score'] > 0 for j in jobs)
    assert body['skill_gap_count'] >= len(body['skill_gaps']) > 0
    for job in body['recommended_jobs']:
        original = graduate.get(f"/api/jobs/{job['id']}").json()
        assert job['employment_type'] == original['employment_type']
        assert {s['name'] for s in job['skills']} == {s['name'] for s in original['skills']}


def test_empty_profile_has_no_invented_competencies(client):
    register(client)
    body = client.get('/api/dashboard').json()
    assert body['readiness'] == 0
    assert body['top_skills'] == []
    assert all(job['score'] == 0 for job in body['recommended_jobs'])
    assert body['recommended_job_count'] == 0
    assert body['desired_role'] is None


def test_dashboard_without_vacancies_does_not_invent_matches(graduate, seeded):
    from app.models import Job
    with seeded() as db:
        for job in db.scalars(select(Job)):
            db.delete(job)
        db.commit()
    body = graduate.get('/api/dashboard').json()
    assert body['recommended_job_count'] == 0
    assert body['recommended_jobs'] == []
    assert body['market_sample_size'] == 0
    assert body['skill_gap_count'] == 0
    assert body['skill_gaps'] == []


def test_dashboard_does_not_replace_an_empty_target_role_with_other_roles(graduate, seeded):
    from app.models import CareerRole
    with seeded() as db:
        role = CareerRole(name='Role Without Vacancies')
        db.add(role)
        db.commit()
        role_id = role.id
    response = graduate.put('/api/profile', json={'name': 'Graduate', 'desired_role_id': role_id})
    assert response.status_code == 200
    body = graduate.get('/api/dashboard').json()
    assert body['desired_role'] == 'Role Without Vacancies'
    assert body['recommended_jobs'] == []
    assert body['recommended_job_count'] == body['market_sample_size'] == body['skill_gap_count'] == 0
    assert body['career_directions']


def test_dashboard_counts_project_evidence_for_requirements_extracted_from_text(admin):
    role_id = admin.post('/api/admin/career-roles', json={'name': 'Text Requirements Role'}).json()['id']
    category_id = admin.get('/api/catalog/job-categories').json()[0]['id']
    response = admin.post('/api/admin/jobs', json={
        'title': 'Text Requirements Vacancy', 'company': 'Example', 'location': 'Astana',
        'description': 'Build services with Python. Python is the required technology.',
        'role_id': role_id, 'category_id': category_id, 'skills': [],
    })
    assert response.status_code == 201
    job_id = response.json()['id']
    assert admin.put('/api/profile', json={'name': 'Administrator', 'desired_role_id': role_id}).status_code == 200
    body = admin.get('/api/dashboard').json()
    assert body['market_sample_size'] == 1
    assert body['readiness_components']['projects'] == 1
    python = next(skill for skill in admin.get('/api/catalog/skills').json() if skill['name'] == 'Python')
    updated = admin.put(f'/api/admin/jobs/{job_id}', json={
        'title': 'Text Requirements Vacancy', 'company': 'Example', 'location': 'Astana',
        'description': 'Build services with Python. Python is the required technology.',
        'role_id': role_id, 'category_id': category_id,
        'skills': [{'skill_id': python['id'], 'level': 1, 'required': True}],
    })
    assert updated.status_code == 200
    assert admin.get('/api/dashboard').json()['readiness_components'] == body['readiness_components']


def test_graduates_cannot_access_admin(graduate):
    for route in ['statistics', 'users', 'jobs', 'skills']:
        assert graduate.get('/api/admin/' + route).status_code == 403
    assert graduate.post('/api/admin/career-roles', json={'name': 'Administrator'}).status_code == 403


def test_admin_job_crud_and_input_validation(admin):
    skill = admin.get('/api/catalog/skills').json()[0]
    role = admin.get('/api/catalog/career-roles').json()[0]
    category = admin.get('/api/catalog/job-categories').json()[0]
    body = {'title': 'New Junior Engineer', 'company': 'Demo Test Company', 'location': 'Astana',
            'description': 'A test vacancy with clearly defined skills and responsibilities.',
            'role_id': role['id'], 'category_id': category['id'], 'salary_min': 200000, 'salary_max': 400000,
            'skills': [{'skill_id': skill['id'], 'required': True, 'level': 1}]}
    created = admin.post('/api/admin/jobs', json=body)
    assert created.status_code == 201, created.text
    identifier = created.json()['id']
    assert created.json()['skills'][0]['weight'] == 2
    assert admin.put(f'/api/admin/jobs/{identifier}', json={**body, 'title': 'Updated Engineer'}).status_code == 200
    assert admin.post('/api/admin/jobs', json={**body, 'salary_max': 100000}).status_code == 422
    assert admin.post('/api/admin/jobs', json={**body, 'skills': body['skills'] * 2}).status_code == 422
    assert admin.delete(f'/api/admin/jobs/{identifier}').status_code == 204


def test_admin_catalog_and_users(admin):
    category = admin.post('/api/admin/skill-categories', json={'name': 'New Category'})
    assert category.status_code == 201
    identifier = category.json()['id']
    skill = admin.post('/api/admin/skills', json={'name': 'New Skill', 'category_id': identifier, 'aliases': ['New Alias']})
    assert skill.status_code == 201
    assert admin.delete(f'/api/admin/skill-categories/{identifier}').status_code == 409
    assert admin.delete('/api/admin/skills/' + str(skill.json()['id'])).status_code == 204
    assert admin.put(f'/api/admin/skill-categories/{identifier}', json={'name': 'Renamed Category'}).status_code == 200
    assert admin.delete(f'/api/admin/skill-categories/{identifier}').status_code == 204
    users = admin.get('/api/admin/users').json()
    me = next(u for u in users if u['role'] == 'admin')
    assert admin.put('/api/admin/users/' + str(me['id']), json={'role': 'graduate', 'active': True}).status_code == 409
    assert admin.delete('/api/admin/users/' + str(me['id'])).status_code == 409
    target = next(u for u in users if u['role'] == 'graduate')
    assert admin.put('/api/admin/users/' + str(target['id']), json={'role': 'graduate', 'active': False}).status_code == 200
    assert admin.post('/api/auth/login', json={'email': target['email'], 'password': os.environ['DEMO_PASSWORD']}).status_code == 401
    assert admin.delete('/api/admin/users/' + str(target['id'])).status_code == 204


def test_seed_is_idempotent(seeded):
    from app.database.seed import seed
    from app.models import Job, Recommendation, Skill, User
    with seeded() as db:
        before = [db.scalar(select(func.count(model.id))) for model in [Job, Skill, User, Recommendation]]
        seed(db)
        after = [db.scalar(select(func.count(model.id))) for model in [Job, Skill, User, Recommendation]]
        assert before == after
        assert before[0] == 30


def test_health_and_openapi(client):
    assert client.get('/api/health').json()['status'] == 'ok'
    schema = client.get('/openapi.json').json()
    assert '/api/projects' in schema['paths']
    assert '/api/jobs/{identifier}/match' in schema['paths']


def test_aliases_cannot_conflict_with_another_skill(admin):
    category = admin.get('/api/catalog/skill-categories').json()[0]['id']
    assert admin.post('/api/admin/skills', json={'name': 'Novel Framework', 'category_id': category, 'aliases': ['JS']}).status_code == 409
    assert admin.post('/api/admin/skills', json={'name': 'Novel Framework', 'category_id': category, 'aliases': ['Novel Framework']}).status_code == 422


def test_catalog_change_marks_analysis_stale(admin):
    job = admin.get('/api/jobs').json()['items'][0]
    match = admin.post(f"/api/jobs/{job['id']}/match").json()
    category = admin.get('/api/catalog/skill-categories').json()[0]['id']
    assert admin.post('/api/admin/skills', json={'name': 'New Technology', 'category_id': category}).status_code == 201
    assert admin.get(f"/api/matches/{match['id']}").json()['stale']
