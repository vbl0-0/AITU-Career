from datetime import date
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints, field_validator, model_validator


class Input(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)


class Register(Input):
    email: EmailStr
    password: Annotated[str, StringConstraints(strip_whitespace=False)] = Field(min_length=10, max_length=128)
    name: str = Field(min_length=2, max_length=150)


class Login(Input):
    email: EmailStr
    password: Annotated[str, StringConstraints(strip_whitespace=False)] = Field(min_length=1, max_length=128)


class ProfileInput(Input):
    name: str = Field(min_length=2, max_length=150)
    phone: str = Field(default='', max_length=40)
    location: str = Field(default='Astana', max_length=150)
    bio: str = Field(default='', max_length=4000)
    desired_role_id: int | None = None
    employment_type: Literal['Full-time', 'Part-time', 'Internship', 'Freelance'] = 'Full-time'
    preferred_location: str = Field(default='Astana', max_length=150)
    preferred_technologies: str = Field(default='', max_length=500)


class EducationInput(Input):
    university: str = Field(default='Astana IT University', min_length=2, max_length=200)
    degree: str = Field(default='Bachelor', min_length=2, max_length=80)
    program: str = Field(min_length=2, max_length=150)
    graduation_year: int = Field(ge=1950, le=2100)


class SkillInput(Input):
    skill_id: int = Field(gt=0)
    level: int = Field(default=2, ge=1, le=3)


class ProjectInput(Input):
    name: str = Field(min_length=2, max_length=150)
    description: str = Field(default='', max_length=5000)
    github_url: str = Field(default='', max_length=500)
    project_type: Literal['Academic', 'Personal', 'Commercial', 'Open source'] = 'Academic'
    skill_ids: list[int] = Field(default_factory=list, max_length=50)


class CertificateInput(Input):
    name: str = Field(min_length=2, max_length=150)
    issuer: str = Field(min_length=2, max_length=150)
    issued_date: date
    credential_url: str = Field(default='', max_length=500)

    @field_validator('issued_date')
    @classmethod
    def issued_in_past(cls, value):
        if value > date.today():
            raise ValueError('Certificate issue date cannot be in the future')
        return value


class ExperienceInput(Input):
    company: str = Field(min_length=2, max_length=150)
    position: str = Field(min_length=2, max_length=150)
    description: str = Field(default='', max_length=5000)
    employment_type: Literal['Full-time', 'Part-time', 'Internship', 'Freelance'] = 'Internship'
    start_date: date
    end_date: date | None = None

    @model_validator(mode='after')
    def valid_dates(self):
        if self.start_date > date.today():
            raise ValueError('Start date cannot be in the future')
        if self.end_date and (self.end_date < self.start_date or self.end_date > date.today()):
            raise ValueError('End date must be between start date and today')
        return self


def validate_url(value):
    if value:
        from urllib.parse import urlparse
        parsed = urlparse(value)
        if parsed.scheme not in {'https', 'http'} or not parsed.netloc or parsed.username or parsed.password:
            raise ValueError('Provide an http(s) URL')
    return value


class Requirement(Input):
    skill_id: int = Field(gt=0)
    required: bool = True
    level: int = Field(default=1, ge=1, le=3)
    weight: float | None = Field(default=None, gt=0, le=10)


class JobInput(Input):
    title: str = Field(min_length=2, max_length=150)
    company: str = Field(min_length=2, max_length=150)
    location: str = Field(min_length=2, max_length=150)
    description: str = Field(min_length=20, max_length=15000)
    employment_type: str = Field(default='Full-time', max_length=30)
    experience_level: str = Field(default='Junior', max_length=50)
    salary_min: int | None = Field(default=None, ge=0)
    salary_max: int | None = Field(default=None, ge=0)
    currency: str = Field(default='KZT', pattern=r'^[A-Z]{3}$')
    role_id: int = Field(gt=0)
    category_id: int = Field(gt=0)
    skills: list[Requirement] = Field(default_factory=list, max_length=100)

    @model_validator(mode='after')
    def valid_salary(self):
        if self.salary_min is not None and self.salary_max is not None and self.salary_max < self.salary_min:
            raise ValueError('Maximum salary cannot be below minimum')
        ids = [s.skill_id for s in self.skills]
        if len(ids) != len(set(ids)):
            raise ValueError('Requirements must be unique')
        return self


class NameInput(Input):
    name: str = Field(min_length=2, max_length=100)


class CatalogSkillInput(NameInput):
    category_id: int = Field(gt=0)
    aliases: list[Annotated[str, StringConstraints(min_length=1, max_length=100)]] = Field(default_factory=list, max_length=20)


class AdminUserInput(Input):
    active: bool
    role: Literal['graduate', 'admin']


class HHImportInput(Input):
    text: str = Field(min_length=2, max_length=150)
    role_id: int = Field(gt=0)
    category_id: int = Field(gt=0)
    area_id: str = Field(default='40', pattern=r'^\d{1,10}$')
    experience: Literal['noExperience', 'between1And3', 'between3And6', 'moreThan6', ''] = 'noExperience'
    limit: int = Field(default=10, ge=1, le=20)


class HHSyncInput(Input):
    role_id: int | None = Field(default=None, gt=0)
    limit: int = Field(default=20, ge=1, le=20)
