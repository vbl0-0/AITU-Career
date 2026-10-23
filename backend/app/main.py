from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.api.routes import admin, auth, jobs, profile
from app.core.config import get_settings
from app.database.session import engine

app = FastAPI(title='AITU Career API', version='1.0.0', description='Explainable competency matching for AITU students and graduates.')
app.add_middleware(CORSMiddleware, allow_origins=get_settings().origins, allow_credentials=True,
                   allow_methods=['GET', 'POST', 'PUT', 'DELETE'], allow_headers=['Authorization', 'Content-Type'])
for router in (auth.router, profile.router, jobs.router, admin.router):
    app.include_router(router, prefix='/api')


@app.get('/api/health', tags=['Health'])
def health():
    with engine.connect() as connection:
        connection.execute(text('SELECT 1'))
    return {'status': 'ok', 'service': 'AITU Career'}
