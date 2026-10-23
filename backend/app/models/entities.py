from datetime import date, datetime, timezone
from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.session import Base


def now():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default='graduate')
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    profile: Mapped['GraduateProfile'] = relationship(back_populates='user', cascade='all, delete-orphan', uselist=False)
    sessions: Mapped[list['AuthSession']] = relationship(cascade='all, delete-orphan')
    saved: Mapped[list['SavedJob']] = relationship(cascade='all, delete-orphan')
    __table_args__ = (CheckConstraint("role IN ('graduate', 'admin')", name='valid_user_role'),)


class AuthSession(Base):
    __tablename__ = 'auth_sessions'
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    refresh_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)


class CareerRole(Base):
    __tablename__ = 'career_roles'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)


class JobCategory(Base):
    __tablename__ = 'job_categories'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)


class GraduateProfile(Base):
    __tablename__ = 'graduate_profiles'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), unique=True)
    name: Mapped[str] = mapped_column(String(150), default='')
    phone: Mapped[str] = mapped_column(String(40), default='')
    location: Mapped[str] = mapped_column(String(150), default='Astana')
    bio: Mapped[str] = mapped_column(Text, default='')
    desired_role_id: Mapped[int | None] = mapped_column(ForeignKey('career_roles.id', ondelete='SET NULL'))
    employment_type: Mapped[str] = mapped_column(String(30), default='Full-time')
    preferred_location: Mapped[str] = mapped_column(String(150), default='Astana')
    preferred_technologies: Mapped[str] = mapped_column(String(500), default='')
    revision: Mapped[int] = mapped_column(Integer, default=1)
    user: Mapped[User] = relationship(back_populates='profile')
    desired_role: Mapped[CareerRole | None] = relationship()
    education: Mapped[list['Education']] = relationship(cascade='all, delete-orphan')
    skills: Mapped[list['UserSkill']] = relationship(cascade='all, delete-orphan')
    projects: Mapped[list['Project']] = relationship(cascade='all, delete-orphan')
    certificates: Mapped[list['Certificate']] = relationship(cascade='all, delete-orphan')
    experience: Mapped[list['Experience']] = relationship(cascade='all, delete-orphan')
    matches: Mapped[list['MatchResult']] = relationship(cascade='all, delete-orphan')
    recommendations: Mapped[list['Recommendation']] = relationship(cascade='all, delete-orphan')


class Education(Base):
    __tablename__ = 'education'
    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey('graduate_profiles.id', ondelete='CASCADE'), index=True)
    university: Mapped[str] = mapped_column(String(200), default='Astana IT University')
    degree: Mapped[str] = mapped_column(String(80), default='Bachelor')
    program: Mapped[str] = mapped_column(String(150))
    graduation_year: Mapped[int] = mapped_column(Integer)
    __table_args__ = (CheckConstraint('graduation_year BETWEEN 1950 AND 2100', name='valid_graduation_year'),)


class SkillCategory(Base):
    __tablename__ = 'skill_categories'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)


class Skill(Base):
    __tablename__ = 'skills'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    category_id: Mapped[int] = mapped_column(ForeignKey('skill_categories.id', ondelete='RESTRICT'), index=True)
    category: Mapped[SkillCategory] = relationship()
    aliases: Mapped[list['SkillAlias']] = relationship(cascade='all, delete-orphan')


class SkillAlias(Base):
    __tablename__ = 'skill_aliases'
    id: Mapped[int] = mapped_column(primary_key=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey('skills.id', ondelete='CASCADE'), index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)


class UserSkill(Base):
    __tablename__ = 'user_skills'
    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey('graduate_profiles.id', ondelete='CASCADE'), index=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey('skills.id', ondelete='RESTRICT'))
    level: Mapped[int] = mapped_column(Integer, default=2)
    skill: Mapped[Skill] = relationship()
    __table_args__ = (UniqueConstraint('profile_id', 'skill_id'), CheckConstraint('level BETWEEN 1 AND 3', name='valid_user_skill_level'))


class Project(Base):
    __tablename__ = 'projects'
    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey('graduate_profiles.id', ondelete='CASCADE'), index=True)
    name: Mapped[str] = mapped_column(String(150))
    description: Mapped[str] = mapped_column(Text, default='')
    github_url: Mapped[str] = mapped_column(String(500), default='')
    project_type: Mapped[str] = mapped_column(String(60), default='Academic')
    technologies: Mapped[list['ProjectSkill']] = relationship(cascade='all, delete-orphan')


class ProjectSkill(Base):
    __tablename__ = 'project_skills'
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey('projects.id', ondelete='CASCADE'), index=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey('skills.id', ondelete='RESTRICT'))
    skill: Mapped[Skill] = relationship()
    __table_args__ = (UniqueConstraint('project_id', 'skill_id'),)


class Certificate(Base):
    __tablename__ = 'certificates'
    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey('graduate_profiles.id', ondelete='CASCADE'), index=True)
    name: Mapped[str] = mapped_column(String(150))
    issuer: Mapped[str] = mapped_column(String(150))
    issued_date: Mapped[date] = mapped_column(Date)
    credential_url: Mapped[str] = mapped_column(String(500), default='')


class Experience(Base):
    __tablename__ = 'experience'
    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey('graduate_profiles.id', ondelete='CASCADE'), index=True)
    company: Mapped[str] = mapped_column(String(150))
    position: Mapped[str] = mapped_column(String(150))
    description: Mapped[str] = mapped_column(Text, default='')
    employment_type: Mapped[str] = mapped_column(String(30), default='Internship')
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    __table_args__ = (CheckConstraint('end_date IS NULL OR end_date >= start_date', name='valid_experience_dates'),)


class Job(Base):
    __tablename__ = 'jobs'
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(150), index=True)
    company: Mapped[str] = mapped_column(String(150))
    location: Mapped[str] = mapped_column(String(150))
    description: Mapped[str] = mapped_column(Text)
    employment_type: Mapped[str] = mapped_column(String(30), default='Full-time')
    experience_level: Mapped[str] = mapped_column(String(50), default='Junior')
    salary_min: Mapped[int | None] = mapped_column(Integer)
    salary_max: Mapped[int | None] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3), default='KZT')
    role_id: Mapped[int] = mapped_column(ForeignKey('career_roles.id', ondelete='RESTRICT'), index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey('job_categories.id', ondelete='RESTRICT'))
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    source: Mapped[str] = mapped_column(String(20), default='manual', server_default='manual')
    external_id: Mapped[str | None] = mapped_column(String(80))
    source_url: Mapped[str | None] = mapped_column(String(500))
    source_published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default='true')
    revision: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    role: Mapped[CareerRole] = relationship()
    category: Mapped[JobCategory] = relationship()
    skills: Mapped[list['JobSkill']] = relationship(cascade='all, delete-orphan')
    saved: Mapped[list['SavedJob']] = relationship(cascade='all, delete-orphan')
    matches: Mapped[list['MatchResult']] = relationship(cascade='all, delete-orphan')
    __table_args__ = (UniqueConstraint('source', 'external_id', name='uq_jobs_source_external_id'), CheckConstraint('salary_min IS NULL OR salary_min >= 0', name='positive_salary_min'), CheckConstraint('salary_max IS NULL OR salary_max >= 0', name='positive_salary_max'), CheckConstraint('salary_min IS NULL OR salary_max IS NULL OR salary_max >= salary_min', name='valid_salary_range'))


class JobSkill(Base):
    __tablename__ = 'job_skills'
    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey('jobs.id', ondelete='CASCADE'), index=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey('skills.id', ondelete='RESTRICT'))
    required: Mapped[bool] = mapped_column(Boolean, default=True)
    level: Mapped[int] = mapped_column(Integer, default=1)
    weight: Mapped[float] = mapped_column(Float, default=2)
    skill: Mapped[Skill] = relationship()
    __table_args__ = (UniqueConstraint('job_id', 'skill_id'), CheckConstraint('level BETWEEN 1 AND 3', name='valid_job_skill_level'), CheckConstraint('weight > 0', name='positive_requirement_weight'))


class SavedJob(Base):
    __tablename__ = 'saved_jobs'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey('jobs.id', ondelete='CASCADE'), index=True)
    job: Mapped[Job] = relationship(back_populates='saved')
    __table_args__ = (UniqueConstraint('user_id', 'job_id'),)


class MatchResult(Base):
    __tablename__ = 'match_results'
    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey('graduate_profiles.id', ondelete='CASCADE'), index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey('jobs.id', ondelete='CASCADE'), index=True)
    score: Mapped[float | None] = mapped_column(Float)
    profile_revision: Mapped[int] = mapped_column(Integer)
    job_revision: Mapped[int] = mapped_column(Integer)
    algorithm_version: Mapped[str] = mapped_column(String(30))
    result: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    recommendations: Mapped[list['Recommendation']] = relationship(cascade='all, delete-orphan', overlaps='recommendations')


class Recommendation(Base):
    __tablename__ = 'recommendations'
    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey('graduate_profiles.id', ondelete='CASCADE'), index=True)
    match_id: Mapped[int] = mapped_column(ForeignKey('match_results.id', ondelete='CASCADE'), index=True)
    content: Mapped[dict] = mapped_column(JSON)
