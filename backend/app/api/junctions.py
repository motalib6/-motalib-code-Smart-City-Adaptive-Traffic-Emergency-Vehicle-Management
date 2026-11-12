"""Junctions API: GET /api/junctions, GET /api/junctions/{id}."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.permissions import get_current_user
from app.database import get_session
from app.models import Junction, User
from app.services.signal_service import demand_for_approach
from app.state import STATE

router = APIRouter(prefix="/api/junctions", tags=["junctions"])


@router.get("")
def list_junctions(session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    rows = session.exec(select(Junction)).all()
    snap = STATE.engine.snapshot() if STATE.engine else {}
    live = snap.get("junctions", {})
    return [
        {
            "id": j.id, "name": j.name, "x": j.x, "y": j.y, "lanes": j.lanes,
            "phase": STATE.phases.get(j.id, "GREEN_NS"),
            "live": live.get(j.id, {}),
            "source": snap.get("source", "simulated"),
        }
        for j in rows
    ]


@router.get("/{junction_id}")
def get_junction(junction_id: str, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    row = session.get(Junction, junction_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Junction not found")
    snap = STATE.engine.snapshot() if STATE.engine else {}
    live = snap.get("junctions", {}).get(junction_id, {})
    counts, queues = live.get("counts", {}), live.get("queues", {})
    demand = {}
    for approach in ("N", "S", "E", "W"):
        demand[approach] = demand_for_approach(
            queues.get(approach, 0), counts.get(approach, 0),
            live.get("avg_wait_s", 0.0), STATE.settings,
        )
    return {
        "id": row.id, "name": row.name, "x": row.x, "y": row.y,
        "phase": STATE.phases.get(junction_id, "GREEN_NS"),
        "live": live, "demand": demand,
        "explanation": (
            "Green duration grows with density D = 0.5*queue + 0.3*count + 0.2*wait, "
            "clipped to [green_min_s, green_max_s]; starved approaches are served "
            "after the configured starvation window."
        ),
        "source": snap.get("source", "simulated"),
    }
