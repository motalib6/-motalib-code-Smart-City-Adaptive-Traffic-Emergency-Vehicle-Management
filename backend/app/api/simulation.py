"""Simulation API: start / pause / reset / scenario / status."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.core.permissions import get_current_user, require_role
from app.database import get_session
from app.models import User
from app.schemas import ScenarioRequest, SimulationStartRequest
from app.services.event_service import log_event
from app.simulation.sumo_engine import SumoEngine, sumo_available
from app.state import STATE

router = APIRouter(prefix="/api/simulation", tags=["simulation"])


@router.get("/status")
def status(user: User = Depends(get_current_user)):
    eng = STATE.engine.status() if STATE.engine else {}
    ok, why = sumo_available()
    return {**eng, "sumo_available": ok, "sumo_detail": why, "engine_source": STATE.engine_source}


@router.post("/start")
async def start(
    body: SimulationStartRequest,
    session: Session = Depends(get_session),
    user: User = Depends(require_role("ADMIN", "OPERATOR")),
):
    if body.engine == "sumo":
        ok, why = sumo_available()
        if not ok:
            raise HTTPException(status_code=503, detail=f"SUMO unavailable: {why}")
    try:
        if hasattr(STATE, "simulation_manager") and STATE.simulation_manager:
            result = await STATE.simulation_manager.start(scenario=body.scenario, engine=body.engine)
            STATE.engine = STATE.simulation_manager.engine
            STATE.engine_source = STATE.simulation_manager.engine.source
        else:
            if body.engine == "sumo":
                STATE.engine = SumoEngine()
                STATE.engine_source = "sumo"
            else:
                from app.simulation.simulated_engine import SimulatedEngine
                STATE.engine = SimulatedEngine()
                STATE.engine_source = "simulated"
            result = STATE.engine.start(body.scenario)
    except (ValueError, RuntimeError) as e:
        raise HTTPException(status_code=422, detail=str(e))
    STATE.running = True
    STATE.settings["scenario"] = body.scenario
    log_event(session, "SIMULATION_STARTED",
              f"engine={STATE.engine_source} scenario={body.scenario}", source=STATE.engine_source)
    return {"status": "started", "engine_source": STATE.engine_source, **result}


@router.post("/pause")
async def pause(session: Session = Depends(get_session), user: User = Depends(require_role("ADMIN", "OPERATOR"))):
    if hasattr(STATE, "simulation_manager") and STATE.simulation_manager:
        result = await STATE.simulation_manager.pause()
    else:
        result = STATE.engine.pause() if STATE.engine else {}
    STATE.running = False
    log_event(session, "SIMULATION_PAUSED", "simulation paused")
    return {"status": "paused", **STATE.engine.status()}


@router.post("/resume")
async def resume(session: Session = Depends(get_session), user: User = Depends(require_role("ADMIN", "OPERATOR"))):
    if hasattr(STATE, "simulation_manager") and STATE.simulation_manager:
        result = await STATE.simulation_manager.resume()
    else:
        if STATE.engine:
            STATE.engine.running = True
            result = STATE.engine.status()
        else:
            result = {}
    STATE.running = True
    log_event(session, "SIMULATION_RESUMED", "simulation resumed")
    return {"status": "resumed", **result}


@router.post("/reset")
async def reset(session: Session = Depends(get_session), user: User = Depends(require_role("ADMIN", "OPERATOR"))):
    if hasattr(STATE, "simulation_manager") and STATE.simulation_manager:
        result = await STATE.simulation_manager.reset()
    else:
        result = STATE.engine.reset() if STATE.engine else {}
    STATE.running = False
    STATE.tick = 0
    STATE.emergency_active = None
    log_event(session, "SIMULATION_RESET", "simulation reset")
    return {"status": "reset", **STATE.engine.status()}


@router.post("/scenario")
async def scenario(
    body: ScenarioRequest,
    session: Session = Depends(get_session),
    user: User = Depends(require_role("ADMIN", "OPERATOR")),
):
    try:
        if hasattr(STATE, "simulation_manager") and STATE.simulation_manager:
            result = await STATE.simulation_manager.set_scenario(body.scenario)
        else:
            result = STATE.engine.set_scenario(body.scenario)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    STATE.settings["scenario"] = body.scenario
    log_event(session, "SCENARIO_CHANGED", f"scenario={body.scenario}")
    return {"status": "ok", **result}
