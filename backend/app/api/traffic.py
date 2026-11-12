"""Traffic API: POST /api/traffic/inject, GET /api/traffic/current."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.permissions import get_current_user, require_role
from app.database import get_session
from app.models import TrafficReading, User
from app.schemas import TrafficInjectRequest
from app.services.event_service import log_event
from app.services.signal_service import demand_for_approach
from app.services.traffic_service import congestion_level, density_score
from app.state import STATE

router = APIRouter(prefix="/api/traffic", tags=["traffic"])


@router.post("/inject", status_code=201)
def inject(
    body: TrafficInjectRequest,
    session: Session = Depends(get_session),
    user: User = Depends(require_role("ADMIN", "OPERATOR")),
):
    if body.junction_id not in ("J1", "J2", "J3", "J4"):
        raise HTTPException(status_code=422, detail="unknown junction_id")
    w = STATE.settings
    density = density_score(
        body.queue_length, body.vehicle_count, body.avg_wait_s,
        w["w_queue"], w["w_count"], w["w_wait"],
    )
    reading = TrafficReading(
        junction_id=body.junction_id, approach=body.approach,
        vehicle_count=body.vehicle_count, queue_length=body.queue_length,
        avg_wait_s=body.avg_wait_s, density_score=round(density, 2), source=body.source,
    )
    session.add(reading)
    session.commit()
    session.refresh(reading)
    decision = demand_for_approach(body.queue_length, body.vehicle_count, body.avg_wait_s, w)
    log_event(session, "TRAFFIC_INJECTED",
              f"{body.junction_id}/{body.approach}: count={body.vehicle_count} "
              f"queue={body.queue_length} density={density:.2f} green={decision['green_s']}s",
              junction_id=body.junction_id, source=body.source)
    return {
        "reading_id": reading.id, "junction_id": body.junction_id,
        "approach": body.approach, "density": round(density, 2),
        "congestion": congestion_level(density),
        "recommended_green_s": decision["green_s"], "source": body.source,
    }


@router.get("/current")
def current(session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    snap = STATE.engine.snapshot() if STATE.engine else {}
    latest = session.exec(
        select(TrafficReading).order_by(TrafficReading.created_at.desc()).limit(20)
    ).all()
    return {
        "source": snap.get("source", "simulated"),
        "simulation": snap,
        "recent_readings": [
            {"junction_id": r.junction_id, "approach": r.approach,
             "vehicle_count": r.vehicle_count, "queue_length": r.queue_length,
             "avg_wait_s": r.avg_wait_s, "density": r.density_score,
             "source": r.source, "created_at": r.created_at.isoformat()}
            for r in latest
        ],
    }
