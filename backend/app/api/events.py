"""Events API: GET /api/events (persisted SQLite event log)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.core.permissions import get_current_user
from app.database import get_session
from app.models import Event, User

router = APIRouter(prefix="/api/events", tags=["events"])


@router.get("")
def list_events(
    type: str | None = None, junction_id: str | None = None, limit: int = 100,
    session: Session = Depends(get_session), user: User = Depends(get_current_user),
):
    q = select(Event).order_by(Event.created_at.desc())
    if type:
        q = q.where(Event.type == type)
    if junction_id:
        q = q.where(Event.junction_id == junction_id)
    rows = session.exec(q.limit(min(limit, 500))).all()
    return [{"id": r.id, "type": r.type, "junction_id": r.junction_id,
             "message": r.message, "source": r.source,
             "created_at": r.created_at.isoformat()} for r in rows]
