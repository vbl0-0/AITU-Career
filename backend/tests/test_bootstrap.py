"""Provisioning tests use the same isolated migrated schema as the API suite."""
import pytest
from sqlalchemy import func, select


@pytest.fixture
def clean_db(database, monkeypatch):
    from app.core.config import get_settings
    from app.database.session import Base
    settings = get_settings()
    monkeypatch.setattr(settings, 'seed_demo', False)
    monkeypatch.setattr(settings, 'bootstrap_admin_email', '')
    monkeypatch.setattr(settings, 'bootstrap_admin_password', '')
    with database() as db:
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(table.delete())
        db.commit()
        yield db


def test_clean_seed_creates_catalog_without_demo_accounts_or_vacancies(clean_db):
    from app.database.seed import seed
    from app.models import CareerRole, Job, JobCategory, Skill, User
    seed(clean_db)
    assert clean_db.scalar(select(func.count(Skill.id))) == 69
    assert clean_db.scalar(select(func.count(CareerRole.id))) == 13
    assert clean_db.scalar(select(func.count(JobCategory.id))) == 5
    assert clean_db.scalar(select(func.count(Job.id))) == 0
    assert clean_db.scalar(select(func.count(User.id))) == 0
    seed(clean_db)
    assert clean_db.scalar(select(func.count(Skill.id))) == 69


def test_explicit_admin_can_sign_in_and_manage_a_clean_install(clean_db):
    from fastapi.testclient import TestClient
    from app.database.bootstrap import bootstrap_admin
    from app.database.seed import seed
    from app.main import app
    from app.models import User
    seed(clean_db)
    password = 'Bootstrap-test-password-42!'
    assert bootstrap_admin(clean_db, email='Owner@aitu.edu.kz', name='Platform Owner', password=password)
    owner = clean_db.scalar(select(User).where(User.email == 'owner@aitu.edu.kz'))
    original_hash = owner.password_hash
    assert not bootstrap_admin(clean_db, email=owner.email, name='Changed Name')
    assert owner.password_hash == original_hash
    assert owner.profile.name == 'Platform Owner'
    assert owner.profile.skills == []
    with TestClient(app) as client:
        login = client.post('/api/auth/login', json={'email': owner.email, 'password': password})
        assert login.status_code == 200
        client.headers['Authorization'] = 'Bearer ' + login.json()['access_token']
        assert client.get('/api/admin/statistics').json()['jobs'] == 0
        assert client.post('/api/admin/career-roles', json={'name': 'Custom Career Role'}).status_code == 201


def test_admin_setup_refuses_existing_graduate_or_disabled_account(clean_db):
    from app.database.bootstrap import bootstrap_admin
    from app.core.security import passwords
    from app.models import GraduateProfile, User
    for address, role, active in [('graduate@aitu.edu.kz', 'graduate', True), ('disabled@aitu.edu.kz', 'admin', False)]:
        user = User(email=address, role=role, active=active, password_hash=passwords.hash('Original-password-42!'))
        user.profile = GraduateProfile(name='Original Name')
        clean_db.add(user)
        clean_db.commit()
        original_hash = user.password_hash
        with pytest.raises(ValueError, match='No changes made'):
            bootstrap_admin(clean_db, email=address, name='Owner', password='Replacement-password-42!')
        assert user.role == role and user.active == active
        assert user.password_hash == original_hash


def test_invalid_admin_password_is_not_disclosed_or_saved(clean_db):
    from app.database.bootstrap import bootstrap_admin
    from app.models import User
    password = 'short-pw'
    with pytest.raises(ValueError) as error:
        bootstrap_admin(clean_db, email='owner@aitu.edu.kz', name='Owner', password=password)
    assert password not in str(error.value)
    assert clean_db.scalar(select(func.count(User.id))) == 0


def test_clean_startup_can_provision_admin_from_explicit_settings(clean_db, monkeypatch):
    from app.core.config import get_settings
    from app.database.seed import seed
    from app.models import Job, User
    settings = get_settings()
    monkeypatch.setattr(settings, 'bootstrap_admin_email', 'owner@aitu.edu.kz')
    monkeypatch.setattr(settings, 'bootstrap_admin_name', 'Owner')
    monkeypatch.setattr(settings, 'bootstrap_admin_password', 'Configured-password-42!')
    seed(clean_db)
    owner = clean_db.scalar(select(User))
    assert owner.role == 'admin'
    assert clean_db.scalar(select(func.count(Job.id))) == 0
    original_hash = owner.password_hash
    monkeypatch.setattr(settings, 'bootstrap_admin_password', '')
    seed(clean_db)
    assert clean_db.scalar(select(func.count(User.id))) == 1
    assert owner.password_hash == original_hash


def test_admin_cli_reads_password_from_stdin_without_printing_it(clean_db, monkeypatch, capsys):
    import io
    from app.database import bootstrap
    from app.core.security import passwords
    from app.models import Job, User
    password = 'CLI-test-password-42!'
    monkeypatch.setattr(bootstrap, 'SessionLocal', lambda: clean_db)
    monkeypatch.setattr('sys.stdin', io.StringIO(password + '\n'))
    bootstrap.main(['--email', 'cli.owner@aitu.edu.kz', '--name', 'CLI Owner', '--password-stdin'])
    output = capsys.readouterr()
    assert password not in output.out + output.err
    owner = clean_db.scalar(select(User).where(User.email == 'cli.owner@aitu.edu.kz'))
    assert owner.role == 'admin' and passwords.verify(password, owner.password_hash)
    assert clean_db.scalar(select(func.count(Job.id))) == 0
