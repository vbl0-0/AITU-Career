from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.core.security import admin_user, current_user
from app.database.session import get_db
from app.models import AuthSession, CareerRole, GraduateProfile, Job, JobCategory, JobSkill, MatchResult, Skill, SkillAlias, SkillCategory, User
from app.repositories.common import commit, require, validate_skills
from app.schemas.inputs import AdminUserInput, CatalogSkillInput, HHImportInput, HHSyncInput, JobInput, NameInput
from app.services.serialization import job as serialize_job, row

router = APIRouter(tags=['Catalog and administration'])


def skill_out(item):
    return {**row(item), 'category': item.category.name, 'aliases': [a.name for a in item.aliases]}


def validate_aliases(body, db, identifier=None):
    terms = [body.name.casefold()] + [a.strip().casefold() for a in body.aliases]
    if len(set(terms)) != len(terms):
        raise HTTPException(422, 'Aliases must be distinct from the skill name and each other')
    for skill in db.scalars(select(Skill)):
        if skill.id != identifier and set(terms) & {skill.name.casefold(), *(a.name.casefold() for a in skill.aliases)}:
            raise HTTPException(409, 'Skill name or alias conflicts with another skill')


def catalog_crud(resource, model, schema=NameInput, serializer=row):
    def listing(user: User = Depends(current_user), db: Session = Depends(get_db)):
        return [serializer(x) for x in db.scalars(select(model).order_by(model.name))]

    def create(body: schema, user: User = Depends(admin_user), db: Session = Depends(get_db)):
        data = body.model_dump(exclude={'aliases'})
        if model == Skill:
            require(db, SkillCategory, body.category_id)
            validate_aliases(body, db)
        duplicate = db.scalar(select(model).where(func.lower(model.name) == body.name.lower()))
        if duplicate:
            raise HTTPException(409, 'Name is already in use')
        item = model(**data)
        if model == Skill:
            item.aliases = [SkillAlias(name=a.strip().lower()) for a in body.aliases if a.strip()]
        db.add(item)
        commit(db)
        db.refresh(item)
        return serializer(item)

    def update(identifier: int, body: schema, user: User = Depends(admin_user), db: Session = Depends(get_db)):
        item = require(db, model, identifier)
        if model == Skill:
            require(db, SkillCategory, body.category_id)
            validate_aliases(body, db, identifier)
        duplicate = db.scalar(select(model).where(func.lower(model.name) == body.name.lower(), model.id != identifier))
        if duplicate:
            raise HTTPException(409, 'Name is already in use')
        for k, v in body.model_dump(exclude={'aliases'}).items():
            setattr(item, k, v)
        if model == Skill:
            item.aliases.clear()
            db.flush()
            item.aliases = [SkillAlias(name=a.strip().lower()) for a in body.aliases if a.strip()]
            for profile in db.scalars(select(GraduateProfile)):
                profile.revision += 1
        commit(db)
        db.refresh(item)
        return serializer(item)

    def delete(identifier: int, user: User = Depends(admin_user), db: Session = Depends(get_db)):
        db.delete(require(db, model, identifier))
        commit(db)

    router.add_api_route(f'/catalog/{resource}', listing, methods=['GET'], name=f'catalog_{resource}', response_model=None)
    router.add_api_route(f'/admin/{resource}', listing, methods=['GET'], dependencies=[Depends(admin_user)], name=f'admin_list_{resource}', response_model=None)
    for method, path, handler, status in [('POST', '', create, 201), ('PUT', '/{identifier}', update, 200), ('DELETE', '/{identifier}', delete, 204)]:
        router.add_api_route(f'/admin/{resource}{path}', handler, methods=[method], status_code=status, name=f'admin_{method.lower()}_{resource}', response_model=None)


catalog_crud('skills', Skill, CatalogSkillInput, skill_out)
catalog_crud('skill-categories', SkillCategory)
catalog_crud('career-roles', CareerRole)
catalog_crud('job-categories', JobCategory)


@router.get('/admin/statistics')
def statistics(user: User = Depends(admin_user), db: Session = Depends(get_db)):
    return {'users': db.scalar(select(func.count(User.id))), 'jobs': db.scalar(select(func.count(Job.id))),
            'skills': db.scalar(select(func.count(Skill.id))), 'matches': db.scalar(select(func.count(MatchResult.id))),
            'average_match': round(db.scalar(select(func.avg(MatchResult.score))) or 0, 1)}


@router.get('/admin/users')
def users(user: User = Depends(admin_user), db: Session = Depends(get_db)):
    return [{**row(item), 'name': item.profile.name} for item in db.scalars(select(User).order_by(User.id))]


@router.put('/admin/users/{identifier}')
def update_user(identifier: int, body: AdminUserInput, user: User = Depends(admin_user), db: Session = Depends(get_db)):
    target = require(db, User, identifier)
    if target.id == user.id and (not body.active or body.role != 'admin'):
        raise HTTPException(409, 'You cannot disable or demote your own admin account')
    target.active, target.role = body.active, body.role
    if not target.active:
        for session in target.sessions:
            session.revoked = True
    commit(db)
    return row(target)


@router.delete('/admin/users/{identifier}', status_code=204)
def delete_user(identifier: int, user: User = Depends(admin_user), db: Session = Depends(get_db)):
    target = require(db, User, identifier)
    if target.id == user.id:
        raise HTTPException(409, 'You cannot delete your own admin account')
    db.delete(target)
    commit(db)


@router.get('/admin/jobs')
def list_jobs(user: User = Depends(admin_user), db: Session = Depends(get_db)):
    return [serialize_job(j) for j in db.scalars(select(Job).order_by(Job.id.desc()))]


def job_values(body, db):
    require(db, CareerRole, body.role_id)
    require(db, JobCategory, body.category_id)
    validate_skills(db, [s.skill_id for s in body.skills])
    return body.model_dump(exclude={'skills'})


def requirements(body):
    return [JobSkill(skill_id=s.skill_id, required=s.required, level=s.level,
                     weight=s.weight if s.weight is not None else 2.0 if s.required else 1.0) for s in body.skills]


@router.post('/admin/jobs', status_code=201)
def create_job(body: JobInput, user: User = Depends(admin_user), db: Session = Depends(get_db)):
    item = Job(**job_values(body, db))
    item.skills = requirements(body)
    db.add(item)
    commit(db)
    db.refresh(item)
    return serialize_job(item)


@router.put('/admin/jobs/{identifier}')
def update_job(identifier: int, body: JobInput, user: User = Depends(admin_user), db: Session = Depends(get_db)):
    item = require(db, Job, identifier)
    for k, v in job_values(body, db).items():
        setattr(item, k, v)
    item.skills.clear()
    db.flush()
    item.skills = requirements(body)
    item.revision += 1
    commit(db)
    db.refresh(item)
    return serialize_job(item)


@router.delete('/admin/jobs/{identifier}', status_code=204)
def delete_job(identifier: int, user: User = Depends(admin_user), db: Session = Depends(get_db)):
    db.delete(require(db, Job, identifier))
    commit(db)


@router.post('/admin/jobs/import/hh')
def import_hh(body: HHImportInput, user: User = Depends(admin_user), db: Session = Depends(get_db)):
    from app.services.hh_import import HHError, synchronize
    try:
        return synchronize(db, body)
    except HHError as error:
        raise HTTPException(502, str(error)) from None


@router.post('/admin/jobs/sync/hh')
def sync_hh(body: HHSyncInput, user: User = Depends(admin_user), db: Session = Depends(get_db)):
    from app.services.hh_import import HHError, synchronize
    try:
        return synchronize(db, body, refresh=True)
    except HHError as error:
        raise HTTPException(502, str(error)) from None
