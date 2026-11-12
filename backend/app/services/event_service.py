"""Event service — persist every important event to SQLite."""
from __future__ import annotations

from sqlmodel import Session

from app.models import Event


def log_event(
    session: Session,
    type_: str,
    message: str,
    junction_id: str | None = None,
    source: str = "system",
) -> Event:
    event = Event(type=type_, junction_id=junction_id, message=message, source=source)
    session.add(event)
    session.commit()
    session.refresh(event)
    return event
