"""SMARTFLOW ODISHA — FastAPI backend entrypoint.

Run from backend/:  uvicorn app.main:app --reload --port 8000
Docs: http://127.0.0.1:8000/docs   Health: GET /api/health
"""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select

from app.api import (
    admin,
    analytics,
    auth,
    dashboard,
    emergencies,
    events,
    junctions,
    simulation,
    traffic,
    v1,
    vision,
)
from app.config import settings
from app.database import create_db_and_tables, engine
from app.models import Junction, TrafficReading
from app.seed import seed_admin
from app.simulation.simulated_engine import SimulatedEngine
from app.simulation.simulation_manager import SimulationManager
from app.simulation.sumo_engine import sumo_available
from app.state import STATE
from app.websocket.manager import manager as ws_manager

JUNCTION_SEED = [
    ("J1", "Junction 1 — Rasulgarh", 150.0, 150.0),
    ("J2", "Junction 2 — Vani Vihar", 150.0, 450.0),
    ("J3", "Junction 3 — Master Canteen", 450.0, 150.0),
    ("J4", "Junction 4 — Khandagiri", 450.0, 450.0),
]


def _seed_junctions() -> None:
    with Session(engine) as session:
        for jid, name, x, y in JUNCTION_SEED:
            j = session.get(Junction, jid)
            if j is None:
                session.add(Junction(id=jid, name=name, x=x, y=y))
            else:
                j.name = name
                j.x = x
                j.y = y
                session.add(j)
        session.commit()


def _save_traffic_snapshot_to_db(snap: dict) -> None:
    """Store periodic traffic snapshot in SQLite for auditing and analytics."""
    junctions = snap.get("junctions", {})
    src = snap.get("source", STATE.engine_source)
    with Session(engine) as session:
        for jid, data in junctions.items():
            counts = data.get("counts", {})
            queues = data.get("queues", {})
            avg_wait = data.get("avg_wait_s", 0.0)
            for app in ("N", "S", "E", "W"):
                c = counts.get(app, 0)
                q = queues.get(app, 0)
                if c > 0 or q > 0:
                    density = round(0.5 * q + 0.3 * c + 0.2 * avg_wait, 2)
                    reading = TrafficReading(
                        junction_id=jid,
                        approach=app,
                        vehicle_count=c,
                        queue_length=q,
                        avg_wait_s=avg_wait,
                        density_score=density,
                        source=src,
                    )
                    session.add(reading)
        session.commit()


async def _handle_telemetry_broadcast(snap: dict) -> None:
    """Unified telemetry broadcaster for WebSocket clients."""
    STATE.tick = snap.get("tick", STATE.tick)
    STATE.engine_source = snap.get("source", STATE.engine_source)

    # Sync phases from SUMO if available
    junctions_data = snap.get("junctions", {})
    for jid, jdata in junctions_data.items():
        if "phase_name" in jdata:
            STATE.phases[jid] = jdata["phase_name"]

    payload = {
        "source": snap.get("source"),
        "tick": snap.get("tick"),
        "sim_time_s": snap.get("sim_time_s", float(snap.get("tick", STATE.tick))),
        "total_vehicles": snap.get("total_vehicles"),
        "waiting_to_depart": snap.get("waiting_to_depart", 0),
        "avg_wait_s": snap.get("avg_wait_s", 0.0),
        "junctions": junctions_data,
        "vehicles": snap.get("vehicles", []),
        "traffic_lights": snap.get("traffic_lights", {}),
        "phases": dict(STATE.phases),
        "emergency": STATE.emergency_active,
    }

    # Broadcast to /ws/live and /ws/telemetry subscribers
    await ws_manager.broadcast("simulation_tick", payload)
    await ws_manager.broadcast("telemetry_update", payload)

    # Periodic SQLite snapshot persistence (every 10 ticks)
    if snap.get("tick", 0) % 10 == 0:
        try:
            _save_traffic_snapshot_to_db(snap)
        except Exception:
            pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    seed_admin()
    _seed_junctions()

    # Initialize SimulationManager as single TraCI owner
    sim_mgr = SimulationManager(
        default_engine_type="simulated",
        gui=False,
        telemetry_callback=_handle_telemetry_broadcast,
    )
    STATE.simulation_manager = sim_mgr
    STATE.engine = sim_mgr.engine
    STATE.engine_source = sim_mgr.engine.source
    await sim_mgr.start_worker()

    yield

    await sim_mgr.stop_worker()


app = FastAPI(title="SMARTFLOW ODISHA API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (auth.router, dashboard.router, junctions.router, traffic.router,
          simulation.router, vision.router, emergencies.router,
          analytics.router, events.router, admin.router, v1.router):
    app.include_router(r)


@app.get("/api/health")
@app.get("/health")
def health():
    ok, why = sumo_available()
    return {
        "status": "ok", "app": settings.app_name, "version": "0.1.0",
        "engine_source": STATE.engine_source,
        "sumo_available": ok, "sumo_detail": why,
        "simulation_running": STATE.running,
    }


@app.websocket("/ws/live")
async def ws_live(ws: WebSocket):
    await ws_manager.connect(ws)
    try:
        await ws_manager.broadcast("connected", {"engine_source": STATE.engine_source})
        while True:
            await ws.receive_text()  # keep-alive / client pings
    except WebSocketDisconnect:
        ws_manager.disconnect(ws)


@app.websocket("/ws/telemetry")
async def ws_telemetry(ws: WebSocket):
    await ws_manager.connect(ws)
    try:
        await ws_manager.broadcast("connected", {"engine_source": STATE.engine_source})
        while True:
            await ws.receive_text()  # keep-alive / client pings
    except WebSocketDisconnect:
        ws_manager.disconnect(ws)
