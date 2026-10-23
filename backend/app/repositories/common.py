from fastapi import HTTPException
from sqlalchemy import select
from app.models import Skill


def owned(db, model, identifier, profile_id):
    item = db.get(model, identifier)
    if not item or item.profile_id != profile_id:
        raise HTTPException(404, 'Item not found')
    return item


def require(db, model, identifier):
    item = db.get(model, identifier)
    if not item:
        raise HTTPException(404, f'{model.__name__} not found')
    return item


def validate_skills(db, ids):
    if len(ids) != len(set(ids)):
        raise HTTPException(422, 'Duplicate skills')
    if len(list(db.scalars(select(Skill).where(Skill.id.in_(ids))))) != len(ids):
        raise HTTPException(422, 'Unknown skill')


def commit(db):
    from sqlalchemy.exc import IntegrityError
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, 'Duplicate value or item is in use')
