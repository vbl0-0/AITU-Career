"""API tests use an isolated PostgreSQL schema and real migrations, never user tables."""
import os
import secrets
from pathlib import Path
from uuid import uuid4
import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

load_dotenv(Path(__file__).resolve().parents[2] / '.env')
os.environ.setdefault('JWT_SECRET', secrets.token_urlsafe(48))
os.environ['SEMANTIC_ENABLED'] = 'false'
os.environ['SEED_DEMO'] = 'true'
os.environ['DEMO_PASSWORD'] = secrets.token_urlsafe(18)
os.environ['COOKIE_SECURE'] = 'false'
os.environ['BOOTSTRAP_ADMIN_EMAIL'] = ''
os.environ['BOOTSTRAP_ADMIN_PASSWORD'] = ''


@pytest.fixture(scope='session')
def database():
    from alembic import command
    from alembic.config import Config
    source = os.environ.get('TEST_DATABASE_URL') or os.environ.get('DATABASE_URL')
    if not source:
        pytest.fail('Set TEST_DATABASE_URL or DATABASE_URL to a reachable PostgreSQL database')
    original = make_url(source)
    if original.get_backend_name() != 'postgresql':
        pytest.fail('Integration tests require PostgreSQL')
    schema = 'test_' + uuid4().hex
    control = create_engine(original, connect_args={'connect_timeout': 5})
    with control.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    query = dict(original.query)
    query['options'] = f'-csearch_path={schema}'
    os.environ['DATABASE_URL'] = original.set(query=query).render_as_string(hide_password=False)
    from app.core.config import get_settings
    get_settings.cache_clear()
    from app.database.session import SessionLocal, engine
    config = Config(str(Path(__file__).resolve().parents[1] / 'alembic.ini'))
    config.set_main_option('script_location', str(Path(__file__).resolve().parents[1] / 'migrations'))
    try:
        command.upgrade(config, 'head')
        yield SessionLocal
    finally:
        engine.dispose()
        with control.begin() as connection:
            connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        control.dispose()


@pytest.fixture
def seeded(database):
    from app.database.session import Base
    from app.database.seed import seed
    with database() as db:
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(table.delete())
        db.commit()
        seed(db)
    return database


@pytest.fixture
def client(seeded):
    from fastapi.testclient import TestClient
    from app.main import app
    with TestClient(app) as client:
        yield client


@pytest.fixture
def graduate(client):
    response = client.post('/api/auth/login', json={'email': 'student.demo@aitu.edu.kz', 'password': os.environ['DEMO_PASSWORD']})
    assert response.status_code == 200, response.text
    client.headers['Authorization'] = 'Bearer ' + response.json()['access_token']
    return client


@pytest.fixture
def admin(client):
    response = client.post('/api/auth/login', json={'email': 'admin.demo@aitu.edu.kz', 'password': os.environ['DEMO_PASSWORD']})
    assert response.status_code == 200, response.text
    client.headers['Authorization'] = 'Bearer ' + response.json()['access_token']
    return client
