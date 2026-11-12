"""Admin API: GET/PUT /api/admin/settings, GET /api/admin/users (ADMIN only)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.permissions import require_role
from app.database import get_session
from app.models import User
from app.schemas import AdminSettingsRequest
from app.state import STATE

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/settings")
def get_settings(user: User = Depends(require_role("ADMIN"))):
    return dict(STATE.settings)


@router.put("/settings")
def put_settings(body: AdminSettingsRequest, user: User = Depends(require_role("ADMIN"))):
    updates = body.model_dump(exclude_none=True)
    if updates.get("green_min_s") is not None and updates.get("green_max_s") is not None:
        if updates["green_min_s"] >= updates["green_max_s"]:
            raise HTTPException(status_code=422, detail="green_min_s must be < green_max_s")
    STATE.settings.update(updates)
    STATE.save_settings()
    return dict(STATE.settings)


@router.get("/users")
def list_users(session: Session = Depends(get_session), user: User = Depends(require_role("ADMIN"))):
    rows = session.exec(select(User)).all()
    return [{"id": r.id, "email": r.email, "role": r.role, "is_active": r.is_active} for r in rows]
