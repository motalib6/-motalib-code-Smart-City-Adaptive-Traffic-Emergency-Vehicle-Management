"""V1 Telemetry, Junctions, Fleet, and Simulation Management endpoints.

Supports:
- GET /api/v1/telemetry/metrics
- GET /api/v1/junctions
- GET /api/v1/emergency/fleet
- POST /api/v1/simulation/start
- POST /api/v1/simulation/pause
- POST /api/v1/simulation/resume
- POST /api/v1/simulation/reset
- GET /api/v1/simulation/status
"""
from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.database import get_session
from app.models import Emergency, Junction
from app.schemas import SimulationStartRequest, ScenarioRequest
from app.services.event_service import log_event
from app.services.signal_service import demand_for_approach
from app.simulation import sumo_available
from app.state import STATE

router = APIRouter(prefix="/api/v1", tags=["v1"])


@router.get("/telemetry/metrics")
def get_telemetry_metrics():
    """Retrieve full live telemetry from the active simulation engine."""
    snap = STATE.engine.snapshot() if STATE.engine else {}
    junctions = snap.get("junctions", {})

    total_vehs = snap.get("total_vehicles", 0)
    avg_wait = snap.get("avg_wait_s", 0.0)
    sim_time = snap.get("sim_time_s", float(snap.get("tick", STATE.tick)))

    # Compute overall network congestion level
    total_queue = sum(sum(j.get("queues", {}).values()) for j in junctions.values())
    congestion_level = "low" if total_queue < 5 else "moderate" if total_queue < 15 else "high"

    return {
        "source": snap.get("source", STATE.engine_source),
        "running": STATE.running,
        "tick": snap.get("tick", STATE.tick),
        "simulation_time_s": sim_time,
        "scenario": snap.get("scenario", STATE.settings.get("scenario", "normal")),
        "total_vehicles": total_vehs,
        "waiting_to_depart": snap.get("waiting_to_depart", 0),
        "average_waiting_time_s": avg_wait,
        "total_queue_length": total_queue,
        "congestion_level": congestion_level,
        "junctions": junctions,
        "vehicles": snap.get("vehicles", []),
        "traffic_lights": snap.get("traffic_lights", {}),
    }


@router.get("/junctions")
def list_v1_junctions(session: Session = Depends(get_session)):
    """List junctions with live SUMO/engine metrics."""
    rows = session.exec(select(Junction)).all()
    snap = STATE.engine.snapshot() if STATE.engine else {}
    live_junctions = snap.get("junctions", {})

    result = []
    for j in rows:
        j_live = live_junctions.get(j.id, {})
        result.append({
            "id": j.id,
            "name": j.name,
            "sumo_id": j_live.get("sumo_id", j.id),
            "x": j.x,
            "y": j.y,
            "lanes": j.lanes,
            "phase": STATE.phases.get(j.id, "GREEN_NS"),
            "phase_index": j_live.get("phase", 0),
            "tls_state": j_live.get("tls_state", ""),
            "counts": j_live.get("counts", {"N": 0, "S": 0, "E": 0, "W": 0}),
            "queues": j_live.get("queues", {"N": 0, "S": 0, "E": 0, "W": 0}),
            "occupancy": j_live.get("occupancy", {"N": 0.0, "S": 0.0, "E": 0.0, "W": 0.0}),
            "waiting_times": j_live.get("waiting_times", {"N": 0.0, "S": 0.0, "E": 0.0, "W": 0.0}),
            "total_vehicles": j_live.get("total", 0),
            "avg_wait_s": j_live.get("avg_wait_s", 0.0),
            "source": snap.get("source", STATE.engine_source),
        })
    return result


@router.get("/emergency/fleet")
def list_emergency_fleet(session: Session = Depends(get_session)):
    """Retrieve active emergency vehicles and fleet status."""
    active_rows = session.exec(
        select(Emergency).where(Emergency.status != "COMPLETED").order_by(Emergency.created_at.desc())
    ).all()

    fleet = []
    for em in active_rows:
        route_list = [r.strip() for r in em.route.split(",") if r.strip()]
        fleet.append({
            "id": em.id,
            "ambulance_id": em.ambulance_id,
            "status": em.status,
            "current_junction": em.current_junction,
            "destination_junction": em.destination_junction,
            "route": route_list,
            "speed_kmh": em.speed_kmh,
            "progress": em.progress,
            "eta_s": em.eta_s,
            "gps_source": "SIMULATED GPS — SUMO Fleet",
            "created_at": em.created_at.isoformat() if em.created_at else None,
        })
    return {
        "count": len(fleet),
        "fleet": fleet,
        "active_emergency": STATE.emergency_active,
    }


@router.get("/simulation/status")
def v1_simulation_status():
    """Retrieve status of simulation engine."""
    eng = STATE.engine.status() if STATE.engine else {}
    ok, why = sumo_available()
    return {
        **eng,
        "sumo_available": ok,
        "sumo_detail": why,
        "engine_source": STATE.engine_source,
        "manager_running": getattr(STATE.simulation_manager, "_running", STATE.running) if hasattr(STATE, "simulation_manager") and STATE.simulation_manager else STATE.running,
        "manager_paused": getattr(STATE.simulation_manager, "_paused", not STATE.running) if hasattr(STATE, "simulation_manager") and STATE.simulation_manager else not STATE.running,
    }


@router.post("/simulation/start")
async def v1_simulation_start(
    body: SimulationStartRequest | None = None,
    session: Session = Depends(get_session),
):
    """Start the simulation via thread-safe SimulationManager."""
    scenario = body.scenario if body else "normal"
    engine_name = body.engine if body else "sumo"

    if engine_name == "sumo":
        ok, why = sumo_available()
        if not ok:
            raise HTTPException(status_code=503, detail=f"SUMO unavailable: {why}")

    if hasattr(STATE, "simulation_manager") and STATE.simulation_manager:
        try:
            res = await STATE.simulation_manager.start(scenario=scenario, engine=engine_name)
        except Exception as e:
            raise HTTPException(status_code=422, detail=str(e))
        STATE.engine = STATE.simulation_manager.engine
        STATE.engine_source = STATE.simulation_manager.engine.source
    else:
        # Fallback direct start
        if engine_name == "sumo":
            from app.simulation import SumoEngine
            STATE.engine = SumoEngine()
            STATE.engine_source = "sumo"
        else:
            from app.simulation import SimulatedEngine
            STATE.engine = SimulatedEngine()
            STATE.engine_source = "simulated"
        res = STATE.engine.start(scenario)

    STATE.running = True
    STATE.settings["scenario"] = scenario
    log_event(session, "SIMULATION_STARTED", f"engine={STATE.engine_source} scenario={scenario}", source=STATE.engine_source)
    return {"status": "started", "engine_source": STATE.engine_source, **res}


@router.post("/simulation/pause")
async def v1_simulation_pause(session: Session = Depends(get_session)):
    """Pause the simulation."""
    if hasattr(STATE, "simulation_manager") and STATE.simulation_manager:
        res = await STATE.simulation_manager.pause()
    else:
        res = STATE.engine.pause() if STATE.engine else {}
    STATE.running = False
    log_event(session, "SIMULATION_PAUSED", "simulation paused")
    return {"status": "paused", **res}


@router.post("/simulation/resume")
async def v1_simulation_resume(session: Session = Depends(get_session)):
    """Resume the simulation."""
    if hasattr(STATE, "simulation_manager") and STATE.simulation_manager:
        res = await STATE.simulation_manager.resume()
    else:
        if STATE.engine:
            STATE.engine.running = True
            res = STATE.engine.status()
        else:
            res = {}
    STATE.running = True
    log_event(session, "SIMULATION_RESUMED", "simulation resumed")
    return {"status": "resumed", **res}


@router.post("/simulation/reset")
async def v1_simulation_reset(session: Session = Depends(get_session)):
    """Reset the simulation."""
    if hasattr(STATE, "simulation_manager") and STATE.simulation_manager:
        res = await STATE.simulation_manager.reset()
    else:
        res = STATE.engine.reset() if STATE.engine else {}
    STATE.running = False
    STATE.tick = 0
    STATE.emergency_active = None
    log_event(session, "SIMULATION_RESET", "simulation reset")
    return {"status": "reset", **res}
