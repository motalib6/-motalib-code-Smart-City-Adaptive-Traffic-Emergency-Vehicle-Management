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
    vision,
)
from app.config import settings
from app.database import create_db_and_tables, engine
from app.models import Junction
from app.seed import seed_admin
from app.simulation.simulated_engine import SimulatedEngine
from app.simulation.sumo_engine import sumo_available
from app.state import STATE
from app.websocket.manager import manager as ws_manager

JUNCTION_SEED = [
    ("J1", "Junction 1 — North-West", 0.0, 400.0),
    ("J2", "Junction 2 — North-East", 400.0, 400.0),
    ("J3", "Junction 3 — South-West", 0.0, 0.0),
    ("J4", "Junction 4 — South-East", 400.0, 0.0),
]


def _seed_junctions() -> None:
    with Session(engine) as session:
        for jid, name, x, y in JUNCTION_SEED:
            if session.get(Junction, jid) is None:
                session.add(Junction(id=jid, name=name, x=x, y=y))
        session.commit()


async def _tick_loop() -> None:
    """Advance the simulation 1 tick/sec while running and broadcast live state."""
    while True:
        await asyncio.sleep(1)
        if STATE.running and STATE.engine is not None:
            snap = STATE.engine.step()
            STATE.tick = snap.get("tick", STATE.tick)
            await ws_manager.broadcast("simulation_tick", {
                "source": snap.get("source"), "tick": snap.get("tick"),
                "total_vehicles": snap.get("total_vehicles"),
                "junctions": snap.get("junctions"),
                "phases": dict(STATE.phases),
                "emergency": STATE.emergency_active,
            })


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    seed_admin()
    _seed_junctions()
    STATE.engine = SimulatedEngine()
    STATE.engine_source = "simulated"
    task = asyncio.create_task(_tick_loop())
    yield
    task.cancel()


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
          analytics.router, events.router, admin.router):
    app.include_router(r)


@app.get("/api/health")
def health():
    ok, why = sumo_available()
    return {
        "status": "ok", "app": settings.app_name, "version": "0.1.0",
        "engine_source": STATE.engine_source,
        "sumo_available": ok, "sumo_detail": why,
        "simulation_running": STATE.running,
    }


@app.websocket("/ws/live")
async def live(ws: WebSocket):
    await ws_manager.connect(ws)
    try:
        await ws_manager.broadcast("connected", {"engine_source": STATE.engine_source})
        while True:
            await ws.receive_text()  # keep-alive / client pings
    except WebSocketDisconnect:
        ws_manager.disconnect(ws)
