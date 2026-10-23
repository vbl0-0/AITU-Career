from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.security import current_user
from app.database.session import get_db
from app.models import CareerRole, Certificate, Education, Experience, Project, ProjectSkill, User, UserSkill
from app.repositories.common import commit, owned, require, validate_skills
from app.schemas.inputs import CertificateInput, EducationInput, ExperienceInput, ProfileInput, ProjectInput, SkillInput, validate_url
from app.services import serialization as out

router = APIRouter(tags=['Graduate profile'])


@router.get('/profile')
def get_profile(user: User = Depends(current_user)):
    return out.profile(user.profile)


@router.put('/profile')
def update_profile(body: ProfileInput, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if body.desired_role_id:
        require(db, CareerRole, body.desired_role_id)
    for key, value in body.model_dump().items():
        setattr(user.profile, key, value)
    user.profile.revision += 1
    commit(db)
    return out.profile(user.profile)


def prepare(db, model, body, existing=None):
    values = body.model_dump()
    if model == UserSkill:
        validate_skills(db, [body.skill_id])
    if model == Project:
        validate_skills(db, body.skill_ids)
        values.pop('skill_ids')
    for field in ('github_url', 'credential_url'):
        if field in values:
            try:
                validate_url(values[field])
            except ValueError as exc:
                raise HTTPException(422, str(exc))
    return values


def crud(resource, model, schema, serializer=out.row):
    def listing(user: User = Depends(current_user), db: Session = Depends(get_db)):
        return [serializer(item) for item in db.scalars(select(model).where(model.profile_id == user.profile.id).order_by(model.id.desc()))]

    def create(body: schema, user: User = Depends(current_user), db: Session = Depends(get_db)):
        item = model(profile_id=user.profile.id, **prepare(db, model, body))
        if model == Project:
            item.technologies = [ProjectSkill(skill_id=identifier) for identifier in body.skill_ids]
        db.add(item)
        user.profile.revision += 1
        commit(db)
        db.refresh(item)
        return serializer(item)

    def update(identifier: int, body: schema, user: User = Depends(current_user), db: Session = Depends(get_db)):
        item = owned(db, model, identifier, user.profile.id)
        for key, value in prepare(db, model, body, item).items():
            setattr(item, key, value)
        if model == Project:
            item.technologies.clear()
            db.flush()
            item.technologies = [ProjectSkill(skill_id=identifier) for identifier in body.skill_ids]
        user.profile.revision += 1
        commit(db)
        db.refresh(item)
        return serializer(item)

    def delete(identifier: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
        item = owned(db, model, identifier, user.profile.id)
        db.delete(item)
        user.profile.revision += 1
        commit(db)

    for method, path, handler, status in [('GET', '', listing, 200), ('POST', '', create, 201),
                                          ('PUT', '/{identifier}', update, 200), ('DELETE', '/{identifier}', delete, 204)]:
        router.add_api_route('/' + resource + path, handler, methods=[method], status_code=status,
                             name=f'{method.lower()}_{resource}', response_model=None)


crud('education', Education, EducationInput)
crud('skills', UserSkill, SkillInput, out.skill)
crud('projects', Project, ProjectInput, out.project)
crud('certificates', Certificate, CertificateInput)
crud('experience', Experience, ExperienceInput)
