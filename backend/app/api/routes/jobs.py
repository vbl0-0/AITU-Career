from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session
from app.ai.matching import ALGORITHM_VERSION, analyze, career_summary, context_fingerprint
from app.core.security import current_user
from app.database.session import get_db
from app.models import Job, MatchResult, Recommendation, SavedJob, Skill, User
from app.repositories.common import commit, require
from app.services.serialization import job as serialize_job

router = APIRouter(tags=['Vacancies and analysis'])


@router.get('/jobs')
def jobs(q: str = Query('', max_length=150), role_id: int | None = None, location: str = Query('', max_length=150),
         employment_type: str = '', sort: str = Query('match', pattern='^(match|recent)$'),
         page: int = Query(1, ge=1), limit: int = Query(12, ge=1, le=100),
         user: User = Depends(current_user), db: Session = Depends(get_db)):
    query = select(Job).where(Job.is_active.is_(True))
    if q:
        escaped = q.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
        query = query.where(or_(Job.title.ilike(f'%{escaped}%', escape='\\'), Job.company.ilike(f'%{escaped}%', escape='\\')))
    if role_id:
        query = query.where(Job.role_id == role_id)
    if location:
        query = query.where(Job.location == location)
    if employment_type:
        query = query.where(Job.employment_type == employment_type)
    catalog = list(db.scalars(select(Skill)))
    saved = set(db.scalars(select(SavedJob.job_id).where(SavedJob.user_id == user.id)))
    items = [{**serialize_job(item), 'score': analyze(user.profile, item, catalog)['score'], 'saved': item.id in saved}
             for item in db.scalars(query.order_by(Job.id.desc()))]
    if sort == 'match':
        items.sort(key=lambda j: j['score'] if j['score'] is not None else -1, reverse=True)
    return {'items': items[(page - 1) * limit:page * limit], 'total': len(items), 'page': page, 'limit': limit}


@router.get('/jobs/{identifier}')
def job_detail(identifier: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    job = require(db, Job, identifier)
    saved = db.scalar(select(SavedJob).where(SavedJob.user_id == user.id, SavedJob.job_id == identifier))
    return {**serialize_job(job), 'saved': bool(saved)}


@router.post('/jobs/{identifier}/match')
def match_job(identifier: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    job = require(db, Job, identifier)
    if not job.is_active:
        raise HTTPException(409, 'jobs.closed')
    result = analyze(user.profile, job, list(db.scalars(select(Skill))))
    item = MatchResult(profile_id=user.profile.id, job_id=job.id, score=result['score'],
                       profile_revision=user.profile.revision, job_revision=job.revision,
                       algorithm_version=ALGORITHM_VERSION, result=result)
    item.recommendations = [Recommendation(profile_id=user.profile.id, content=r) for r in result['recommendations']]
    db.add(item)
    commit(db)
    return {**result, 'id': item.id, 'stale': False, 'created_at': item.created_at}


@router.get('/matches/{identifier}')
def get_match(identifier: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    item = db.get(MatchResult, identifier)
    if not item or item.profile_id != user.profile.id:
        raise HTTPException(404, 'Match not found')
    job = require(db, Job, item.job_id)
    stale = (item.profile_revision != user.profile.revision or item.job_revision != job.revision or item.algorithm_version != ALGORITHM_VERSION
             or item.result.get('context_fingerprint') != context_fingerprint(list(db.scalars(select(Skill)))))
    return {**item.result, 'id': item.id, 'stale': stale, 'created_at': item.created_at}


@router.get('/saved-jobs')
def saved_jobs(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return [serialize_job(item.job) for item in db.scalars(select(SavedJob).where(SavedJob.user_id == user.id).order_by(SavedJob.id.desc()))]


@router.post('/saved-jobs/{identifier}', status_code=201)
def save_job(identifier: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    require(db, Job, identifier)
    item = db.scalar(select(SavedJob).where(SavedJob.user_id == user.id, SavedJob.job_id == identifier))
    if not item:
        item = SavedJob(user_id=user.id, job_id=identifier)
        db.add(item)
        commit(db)
    return {'job_id': identifier, 'saved': True}


@router.delete('/saved-jobs/{identifier}', status_code=204)
def unsave_job(identifier: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    item = db.scalar(select(SavedJob).where(SavedJob.user_id == user.id, SavedJob.job_id == identifier))
    if item:
        db.delete(item)
        commit(db)


@router.get('/dashboard')
@router.get('/recommendations')
def dashboard(user: User = Depends(current_user), db: Session = Depends(get_db)):
    result = career_summary(user.profile, list(db.scalars(select(Job).where(Job.is_active.is_(True)))), list(db.scalars(select(Skill))))
    saved = set(db.scalars(select(SavedJob.job_id).where(SavedJob.user_id == user.id)))
    for job in result['recommended_jobs']:
        job['saved'] = job['id'] in saved
    return result
