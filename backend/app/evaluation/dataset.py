"""Strict, database-free input contract for reproducible ranking experiments.

The ``independent`` flag describes the supplied annotation provenance. Validation
checks completeness and agreement records; it cannot establish who made ratings.
"""
import hashlib
import json
from pathlib import Path
import re
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator


NonBlank = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
SkillId = Annotated[int, Field(strict=True, gt=0)]
Level = Annotated[int, Field(strict=True, ge=1, le=3)]
Grade = Annotated[int, Field(strict=True, ge=0, le=3)]


class InputModel(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, str_strip_whitespace=True, allow_inf_nan=False)


def _unique(values, label):
    seen = set()
    for value in values:
        if value in seen:
            raise ValueError(f'Duplicate {label}: {value}')
        seen.add(value)
    return seen


def _term(value):
    return re.sub(r'\s+', ' ', value.casefold()).strip()


class Skill(InputModel):
    id: SkillId
    name: NonBlank
    aliases: list[NonBlank] = Field(default_factory=list)


class Requirement(InputModel):
    skill_id: SkillId
    level: Level
    weight: Annotated[float, Field(gt=0, allow_inf_nan=False)]
    required: bool = True


class Job(InputModel):
    id: NonBlank
    title: NonBlank
    description: str = ''
    requirements: list[Requirement] = Field(default_factory=list)

    @model_validator(mode='after')
    def unique_requirements(self) -> Self:
        _unique((item.skill_id for item in self.requirements), f'requirement skill ID in job {self.id}')
        return self


class ProfileSkill(InputModel):
    skill_id: SkillId
    level: Level


class Project(InputModel):
    name: NonBlank
    description: str = ''
    skill_ids: list[SkillId] = Field(default_factory=list)

    @model_validator(mode='after')
    def unique_skills(self) -> Self:
        _unique(self.skill_ids, f'project skill ID in {self.name}')
        return self


class Experience(InputModel):
    company: NonBlank
    position: NonBlank
    description: str = ''


class Certificate(InputModel):
    name: NonBlank


class Profile(InputModel):
    id: NonBlank
    split: Literal['dev', 'test']
    language: Literal['kk', 'ru', 'en']
    candidate_job_ids: list[NonBlank] = Field(min_length=1)
    skills: list[ProfileSkill] = Field(default_factory=list)
    projects: list[Project] = Field(default_factory=list)
    experience: list[Experience] = Field(default_factory=list)
    certificates: list[Certificate] = Field(default_factory=list)

    @model_validator(mode='after')
    def unique_candidates_and_skills(self) -> Self:
        _unique(self.candidate_job_ids, f'candidate job ID in profile {self.id}')
        _unique((item.skill_id for item in self.skills), f'profile skill ID in {self.id}')
        return self


class Rating(InputModel):
    assessor_id: NonBlank
    grade: Grade


class Judgment(InputModel):
    profile_id: NonBlank
    job_id: NonBlank
    ratings: list[Rating] = Field(min_length=1)
    adjudicated_grade: Grade | None = None

    @model_validator(mode='after')
    def resolve_ratings(self) -> Self:
        _unique((item.assessor_id for item in self.ratings), 'assessor ID in a judgment')
        grades = {item.grade for item in self.ratings}
        if len(grades) == 1:
            if self.adjudicated_grade is not None and self.adjudicated_grade not in grades:
                raise ValueError('Adjudicated grade contradicts agreeing ratings')
        elif self.adjudicated_grade is None:
            raise ValueError('Disagreeing ratings require an adjudicated_grade')
        return self

    @property
    def grade(self) -> int:
        return self.adjudicated_grade if self.adjudicated_grade is not None else self.ratings[0].grade


class Dataset(InputModel):
    schema_version: Literal[1]
    dataset_id: NonBlank
    kind: Literal['synthetic', 'independent']
    catalog: list[Skill] = Field(min_length=1)
    jobs: list[Job] = Field(min_length=1)
    profiles: list[Profile] = Field(min_length=1)
    judgments: list[Judgment] = Field(min_length=1)

    @field_validator('schema_version', mode='before')
    @classmethod
    def integer_schema_version(cls, value):
        if type(value) is not int:
            raise ValueError('schema_version must be the integer 1')
        return value

    @model_validator(mode='after')
    def validate_references(self) -> Self:
        skill_ids = _unique((skill.id for skill in self.catalog), 'catalog skill ID')
        job_ids = _unique((job.id for job in self.jobs), 'job ID')
        profile_ids = _unique((profile.id for profile in self.profiles), 'profile ID')
        terms = {}
        for skill in self.catalog:
            for value in [skill.name, *skill.aliases]:
                term = _term(value)
                if term in terms and terms[term] != skill.id:
                    raise ValueError(f'Ambiguous catalog term {value!r} across skill IDs')
                terms[term] = skill.id
        for job in self.jobs:
            for requirement in job.requirements:
                if requirement.skill_id not in skill_ids:
                    raise ValueError(f'Unknown skill ID {requirement.skill_id} in job {job.id}')
        expected = set()
        for profile in self.profiles:
            for job_id in profile.candidate_job_ids:
                if job_id not in job_ids:
                    raise ValueError(f'Unknown candidate job ID {job_id} in profile {profile.id}')
                expected.add((profile.id, job_id))
            used_skills = [item.skill_id for item in profile.skills]
            used_skills += [skill_id for project in profile.projects for skill_id in project.skill_ids]
            for skill_id in used_skills:
                if skill_id not in skill_ids:
                    raise ValueError(f'Unknown skill ID {skill_id} in profile {profile.id}')
        actual = set()
        for judgment in self.judgments:
            if judgment.profile_id not in profile_ids:
                raise ValueError(f'Unknown judgment profile ID {judgment.profile_id}')
            if judgment.job_id not in job_ids:
                raise ValueError(f'Unknown judgment job ID {judgment.job_id}')
            pair = (judgment.profile_id, judgment.job_id)
            if pair in actual:
                raise ValueError(f'Duplicate judgment pair: {pair}')
            actual.add(pair)
            if self.kind == 'independent' and len(judgment.ratings) < 2:
                raise ValueError('Independent judgments require at least two distinct assessors per pair')
        if actual != expected:
            missing = sorted(expected - actual)
            extra = sorted(actual - expected)
            raise ValueError(f'Judgments must exactly cover candidate pairs; missing={missing}; extra={extra}')
        return self


def _object_without_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'Duplicate JSON object key: {key}')
        result[key] = value
    return result


def _reject_json_constant(value):
    raise ValueError(f'Non-finite JSON number is not supported: {value}')


def parse_dataset(raw: bytes) -> Dataset:
    """Validate the exact input bytes that the runner fingerprints."""
    payload = json.loads(raw.decode('utf-8-sig'),
                         object_pairs_hook=_object_without_duplicate_keys,
                         parse_constant=_reject_json_constant)
    return Dataset.model_validate(payload)


def load_dataset(path: str | Path) -> Dataset:
    """Load UTF-8 JSON without accepting duplicate object keys or NaN/Infinity."""
    return parse_dataset(Path(path).read_bytes())


def dataset_hash(path: str | Path) -> str:
    """Hash the exact supplied file, including annotation and split records."""
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
