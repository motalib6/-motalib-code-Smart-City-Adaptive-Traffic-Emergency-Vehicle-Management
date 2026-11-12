"""Role-based access control: ADMIN / OPERATOR / VIEWER.

ADMIN: manage users, change signal config, all reports.
OPERATOR: start/pause/reset sim, switch scenarios, upload video, request emergency.
VIEWER: read-only dashboard / junctions / analytics / events.
"""
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session, select

from app.core.security import decode_token
from app.database import get_session
from app.models import User

bearer = HTTPBearer(auto_error=False)

ROLE_RANK = {"VIEWER": 1, "OPERATOR": 2, "ADMIN": 3}


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    session: Session = Depends(get_session),
) -> User:
    if creds is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = decode_token(creds.credentials)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = session.exec(select(User).where(User.email == payload.get("sub"))).first()
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def require_role(*roles: str):
    def _check(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return user

    return _check
