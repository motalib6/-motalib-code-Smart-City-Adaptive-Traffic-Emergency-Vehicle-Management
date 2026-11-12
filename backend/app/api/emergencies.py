"""Emergency API: create / location / complete.

Safe priority: the conflicting green is terminated through the signal
state machine (GREEN -> YELLOW -> ALL_RED -> emergency green). The walk
is logged step by step; a direct green-to-green jump is impossible.
GPS is SIMULATED (labelled as such in every response).
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.permissions import get_current_user, require_role
from app.database import get_session
from app.models import Emergency, User
from app.safety.signal_state_machine import SignalStateMachine
from app.schemas import EmergencyCreateRequest, EmergencyLocationRequest
from app.services import emergency_service as es
from app.services.event_service import log_event
from app.state import STATE

router = APIRouter(prefix="/api/emergencies", tags=["emergencies"])

# Per-junction state machines, seeded from STATE.phases.
_machines: dict[str, SignalStateMachine] = {}


def _machine(jid: str) -> SignalStateMachine:
    if jid not in _machines:
        _machines[jid] = SignalStateMachine(jid, STATE.phases.get(jid, "GREEN_NS"))
    return _machines[jid]


@router.post("", status_code=201)
def create(
    body: EmergencyCreateRequest,
    session: Session = Depends(get_session),
    user: User = Depends(require_role("ADMIN", "OPERATOR")),
):
    route = body.route or [body.current_junction, body.destination_junction]
    try:
        route = es.validate_route(route)
    except es.InvalidRouteError as e:
        raise HTTPException(status_code=422, detail=str(e))
    if route[0] != body.current_junction or route[-1] != body.destination_junction:
        raise HTTPException(status_code=422, detail="route must start at current_junction and end at destination_junction")

    emergency = Emergency(
        ambulance_id=body.ambulance_id, current_junction=body.current_junction,
        destination_junction=body.destination_junction, route=",".join(route),
        status="REQUESTED", speed_kmh=body.speed_kmh,
    )
    session.add(emergency)
    session.commit()
    session.refresh(emergency)

    log_event(session, "EMERGENCY_REQUESTED",
              f"{body.ambulance_id} route {'->'.join(route)}", source="simulated-gps")
    log_event(session, "ROUTE_VALIDATED", f"route {'->'.join(route)} valid",
              junction_id=body.current_junction, source="simulated-gps")

    # Safe priority at the current junction.
    nxt = es.next_junction(route, body.current_junction)
    approach = es.approach_for_leg(body.current_junction, nxt) if nxt else "N"
    target_green = es.green_for_approach(approach)
    machine = _machine(body.current_junction)
    steps = machine.force_safe_switch(target_green)
    for s in steps:
        if s.startswith("YELLOW"):
            log_event(session, "YELLOW_STARTED", f"{body.current_junction} yellow clearance",
                      junction_id=body.current_junction)
        elif s == "ALL_RED":
            log_event(session, "ALL_RED_STARTED", f"{body.current_junction} all-red clearance",
                      junction_id=body.current_junction)
    STATE.phases[body.current_junction] = machine.phase
    emergency.status = "PRIORITY_GRANTED"
    session.add(emergency)
    session.commit()
    log_event(session, "PRIORITY_GRANTED",
              f"{body.ambulance_id} green {target_green} at {body.current_junction} "
              f"(via {' -> '.join(steps) or 'already green'})",
              junction_id=body.current_junction)

    eta = es.eta_seconds(es.EDGE_LENGTH_M, body.speed_kmh) if nxt else 0.0
    if nxt:
        log_event(session, "NEXT_JUNCTION_PREPARED",
                  f"{nxt} prepared for {body.ambulance_id}, ETA {eta}s",
                  junction_id=nxt, source="simulated-gps")
    STATE.emergency_active = {
        "id": emergency.id, "ambulance_id": body.ambulance_id,
        "route": route, "current_junction": body.current_junction,
        "destination_junction": body.destination_junction,
        "next_junction": nxt, "eta_s": eta, "status": "PRIORITY_GRANTED",
        "gps_source": "SIMULATED GPS — not a real ambulance feed",
        "safe_transition_steps": steps,
    }
    return {"id": emergency.id, "ambulance_id": body.ambulance_id, "route": route,
            "status": emergency.status, "next_junction": nxt, "eta_s": eta,
            "safe_transition_steps": steps, "gps_source": "SIMULATED GPS"}


@router.get("")
def list_emergencies(session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    rows = session.exec(select(Emergency).order_by(Emergency.created_at.desc()).limit(50)).all()
    return [{"id": r.id, "ambulance_id": r.ambulance_id, "route": r.route,
             "current_junction": r.current_junction, "destination_junction": r.destination_junction,
             "status": r.status, "progress": r.progress, "eta_s": r.eta_s,
             "created_at": r.created_at.isoformat()} for r in rows]


@router.post("/{emergency_id}/location")
def location(
    emergency_id: int, body: EmergencyLocationRequest,
    session: Session = Depends(get_session),
    user: User = Depends(require_role("ADMIN", "OPERATOR")),
):
    emergency = session.get(Emergency, emergency_id)
    if emergency is None:
        raise HTTPException(status_code=404, detail="Emergency not found")
    if emergency.status == "COMPLETED":
        raise HTTPException(status_code=422, detail="Emergency already completed")
    route = emergency.route.split(",") if emergency.route else []
    if body.junction_id:
        if body.junction_id not in route:
            raise HTTPException(status_code=422, detail="junction not on route")
        if body.junction_id != emergency.current_junction:
            log_event(session, "AMBULANCE_PASSED",
                      f"{emergency.ambulance_id} passed {emergency.current_junction}",
                      junction_id=emergency.current_junction, source="simulated-gps")
            emergency.current_junction = body.junction_id
    if body.progress is not None:
        emergency.progress = max(0.0, min(1.0, body.progress))
    if body.speed_kmh:
        emergency.speed_kmh = body.speed_kmh
    nxt = es.next_junction(route, emergency.current_junction)
    emergency.eta_s = es.eta_seconds(es.EDGE_LENGTH_M, emergency.speed_kmh) if nxt else 0.0
    emergency.status = "EN_ROUTE"
    session.add(emergency)
    session.commit()
    if STATE.emergency_active and STATE.emergency_active.get("id") == emergency_id:
        STATE.emergency_active.update({
            "current_junction": emergency.current_junction, "next_junction": nxt,
            "eta_s": emergency.eta_s, "progress": emergency.progress, "status": "EN_ROUTE",
        })
        if nxt:
            log_event(session, "NEXT_JUNCTION_PREPARED",
                      f"{nxt} prepared, ETA {emergency.eta_s}s", junction_id=nxt,
                      source="simulated-gps")
    return {"id": emergency.id, "current_junction": emergency.current_junction,
            "next_junction": nxt, "eta_s": emergency.eta_s,
            "progress": emergency.progress, "gps_source": "SIMULATED GPS"}


@router.post("/{emergency_id}/complete")
def complete(
    emergency_id: int,
    session: Session = Depends(get_session),
    user: User = Depends(require_role("ADMIN", "OPERATOR")),
):
    emergency = session.get(Emergency, emergency_id)
    if emergency is None:
        raise HTTPException(status_code=404, detail="Emergency not found")
    emergency.status = "COMPLETED"
    emergency.completed_at = datetime.now(timezone.utc)
    session.add(emergency)
    session.commit()
    log_event(session, "PRIORITY_RELEASED",
              f"{emergency.ambulance_id} priority released at {emergency.current_junction}",
              junction_id=emergency.current_junction)
    log_event(session, "EMERGENCY_COMPLETED",
              f"{emergency.ambulance_id} reached {emergency.destination_junction}")
    if STATE.emergency_active and STATE.emergency_active.get("id") == emergency_id:
        STATE.emergency_active = None
    return {"id": emergency.id, "status": "COMPLETED"}
