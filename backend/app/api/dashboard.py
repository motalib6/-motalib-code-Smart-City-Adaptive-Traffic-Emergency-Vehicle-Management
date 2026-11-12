"""Dashboard API: GET /api/dashboard/summary (live engine snapshot + DB)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import Session, func, select

from app.core.permissions import get_current_user
from app.database import get_session
from app.models import Event, TrafficReading, User
from app.services.analytics_service import summary as analytics_summary
from app.state import STATE

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary")
def dashboard_summary(
    session: Session = Depends(get_session), user: User = Depends(get_current_user)
):
    snap = STATE.engine.snapshot() if STATE.engine else {}
    junctions = snap.get("junctions", {})
    total_wait = sum(j.get("avg_wait_s", 0) for j in junctions.values()) if junctions else 0
    n_j = len(junctions) or 1
    return {
        "source": snap.get("source", "simulated"),
        "simulation_running": snap.get("running", False),
        "scenario": snap.get("scenario", STATE.settings.get("scenario")),
        "tick": snap.get("tick", 0),
        "total_vehicles": snap.get("total_vehicles", 0),
        "active_junctions": len(junctions),
        "avg_wait_s": round(total_wait / n_j, 2),
        "active_emergencies": 1 if STATE.emergency_active else 0,
        "emergency": STATE.emergency_active,
        "phases": dict(STATE.phases),
        "junctions": junctions,
        "analytics": analytics_summary(session),
        "settings": STATE.settings,
    }
