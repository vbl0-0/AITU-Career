import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from uuid import uuid4
import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.database.session import get_db
from app.models import AuthSession, User

passwords = PasswordHash.recommended()
bearer = HTTPBearer(auto_error=False)
DUMMY_HASH = passwords.hash(secrets.token_urlsafe(32))


def hash_refresh(value):
    return hashlib.sha256(value.encode()).hexdigest()


def utc(value):
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def access_token(user, session):
    settings = get_settings()
    now = datetime.now(timezone.utc)
    return jwt.encode({'sub': str(user.id), 'sid': session.id, 'type': 'access', 'iat': now,
                       'exp': now + timedelta(minutes=settings.access_minutes)}, settings.jwt_secret, algorithm='HS256')


def issue_session(db, user):
    refresh = secrets.token_urlsafe(48)
    session = AuthSession(id=str(uuid4()), user_id=user.id, refresh_hash=hash_refresh(refresh),
                          expires_at=datetime.now(timezone.utc) + timedelta(days=get_settings().session_days))
    db.add(session)
    db.commit()
    return session, refresh


def current_user(request: Request, credentials: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)):
    error = HTTPException(401, 'Authentication required', headers={'WWW-Authenticate': 'Bearer'})
    if not credentials:
        raise error
    try:
        data = jwt.decode(credentials.credentials, get_settings().jwt_secret, algorithms=['HS256'],
                          options={'require': ['sub', 'sid', 'exp', 'iat', 'type']})
        if data['type'] != 'access':
            raise error
        session = db.get(AuthSession, data['sid'])
        user = db.get(User, int(data['sub']))
        if not session or session.revoked or utc(session.expires_at) <= datetime.now(timezone.utc) or not user or not user.active or session.user_id != user.id:
            raise error
        request.state.session_id = session.id
        return user
    except (jwt.InvalidTokenError, ValueError, TypeError, KeyError):
        raise error


def admin_user(user: User = Depends(current_user)):
    if user.role != 'admin':
        raise HTTPException(403, 'Administrator access required')
    return user


def cookie_origin(request: Request):
    origin = request.headers.get('origin')
    if origin and origin.rstrip('/') not in get_settings().origins:
        raise HTTPException(403, 'Origin not allowed')
