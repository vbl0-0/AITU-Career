from functools import lru_cache
from pathlib import Path
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / '.env', extra='ignore')
    database_url: str = 'postgresql+psycopg://aitu@127.0.0.1:55432/aitu_career'
    jwt_secret: str = Field(min_length=32)
    cors_origins: str = 'http://localhost:5173,http://localhost:8080'
    cookie_secure: bool = False
    access_minutes: int = 15
    session_days: int = 7
    seed_demo: bool = True
    demo_password: str = ''
    bootstrap_admin_email: str = ''
    bootstrap_admin_name: str = 'Platform Administrator'
    bootstrap_admin_password: str = ''
    hh_access_token: str = ''
    hh_user_agent: str = 'AITU-Career/1.0'
    hh_timeout_seconds: float = Field(default=10, gt=0, le=30)
    semantic_enabled: bool = False
    semantic_model: str = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
    semantic_threshold: float = Field(default=0.85, ge=0, le=1)
    readiness_market_weight: float = Field(default=0.60, ge=0)
    readiness_projects_weight: float = Field(default=0.15, ge=0)
    readiness_experience_weight: float = Field(default=0.10, ge=0)
    readiness_certificates_weight: float = Field(default=0.05, ge=0)
    readiness_education_weight: float = Field(default=0.10, ge=0)

    @model_validator(mode='after')
    def readiness_has_weight(self):
        if sum(getattr(self, f'readiness_{key}_weight') for key in ('market', 'projects', 'experience', 'certificates', 'education')) <= 0:
            raise ValueError('At least one readiness component must have a positive weight')
        return self

    @field_validator('jwt_secret')
    @classmethod
    def reject_placeholder(cls, value):
        if value.lower() in {'change_me', 'your-secret-key'} or len(set(value)) < 8:
            raise ValueError('JWT_SECRET must be a generated secret of at least 32 characters')
        return value

    @property
    def origins(self):
        return [x.strip().rstrip('/') for x in self.cors_origins.split(',') if x.strip()]


@lru_cache
def get_settings():
    return Settings()
