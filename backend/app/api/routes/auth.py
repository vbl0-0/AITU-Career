import secrets
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.core.security import DUMMY_HASH, access_token, cookie_origin, current_user, hash_refresh, issue_session, passwords, utc
from app.database.session import get_db
from app.models import AuthSession, GraduateProfile, User
from app.repositories.common import commit
from app.schemas.inputs import Login, Register

router = APIRouter(prefix='/auth', tags=['Authentication'])
COOKIE = 'aitu_refresh'


def set_cookie(response, refresh):
    settings = get_settings()
    response.set_cookie(COOKIE, refresh, httponly=True, secure=settings.cookie_secure,
                        samesite='strict', max_age=settings.session_days * 86400, path='/api/auth')


def payload(user, session):
    return {'access_token': access_token(user, session), 'token_type': 'bearer',
            'user': {'id': user.id, 'email': user.email, 'role': user.role, 'name': user.profile.name}}


@router.post('/register', status_code=201, dependencies=[Depends(cookie_origin)])
def register(body: Register, response: Response, db: Session = Depends(get_db)):
    email = str(body.email).lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(409, 'Email is already registered')
    user = User(email=email, password_hash=passwords.hash(body.password), role='graduate')
    user.profile = GraduateProfile(name=body.name)
    db.add(user)
    commit(db)
    session, refresh = issue_session(db, user)
    set_cookie(response, refresh)
    return payload(user, session)


@router.post('/login', dependencies=[Depends(cookie_origin)])
def login(body: Login, response: Response, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == str(body.email).lower()))
    valid = passwords.verify(body.password, user.password_hash if user else DUMMY_HASH)
    if not user or not valid or not user.active:
        raise HTTPException(401, 'Invalid email or password')
    session, refresh = issue_session(db, user)
    set_cookie(response, refresh)
    return payload(user, session)


@router.post('/refresh', dependencies=[Depends(cookie_origin)])
def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get(COOKIE)
    if not token:
        raise HTTPException(401, 'No refresh session')
    session = db.scalar(select(AuthSession).where(AuthSession.refresh_hash == hash_refresh(token)).with_for_update())
    if not session or session.revoked or utc(session.expires_at) <= datetime.now(timezone.utc):
        raise HTTPException(401, 'Session expired')
    user = db.get(User, session.user_id)
    if not user or not user.active:
        raise HTTPException(401, 'Account unavailable')
    rotated = secrets.token_urlsafe(48)
    session.refresh_hash = hash_refresh(rotated)
    db.commit()
    set_cookie(response, rotated)
    return payload(user, session)


@router.post('/logout', status_code=204, dependencies=[Depends(cookie_origin)])
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get(COOKIE)
    if token:
        session = db.scalar(select(AuthSession).where(AuthSession.refresh_hash == hash_refresh(token)))
        if session:
            session.revoked = True
            db.commit()
    response.delete_cookie(COOKIE, path='/api/auth', httponly=True, samesite='strict', secure=get_settings().cookie_secure)


@router.get('/me')
def me(user: User = Depends(current_user)):
    return {'id': user.id, 'email': user.email, 'role': user.role, 'name': user.profile.name}
