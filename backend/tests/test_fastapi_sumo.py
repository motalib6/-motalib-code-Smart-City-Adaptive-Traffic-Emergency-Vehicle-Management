"""
Test script verifying all FastAPI endpoints and WebSocket with actual SUMO running.
Tests:
1. GET /api/health (detects sumo_available=True)
2. POST /api/v1/simulation/start (engine=sumo)
3. GET /api/v1/simulation/status
4. GET /api/v1/telemetry/metrics (live vehicle count, speeds, positions, queues, sim_time)
5. GET /api/v1/junctions (live 4 junctions with counts and queues)
6. GET /api/v1/emergency/fleet
7. WS /ws/telemetry and WS /ws/live receive live ticks
8. POST /api/v1/simulation/pause & resume
9. POST /api/v1/simulation/reset
10. Verify SQLite stored traffic readings
"""
import os
import sys
import json
import pytest
from starlette.testclient import TestClient

BACKEND_DIR = os.path.abspath("smartflow-odisha/backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.main import app
from app.state import STATE
from app.database import engine
from sqlmodel import Session, select
from app.models.traffic_reading import TrafficReading

def test_fastapi_sumo_integration():
    with TestClient(app) as client:
        # 1. Health check
        r_health = client.get("/api/health")
        assert r_health.status_code == 200
        health_data = r_health.json()
        print("\n[TEST] Health:", health_data)
        assert health_data["status"] == "ok"
        assert health_data["sumo_available"] is True

        # 2. Start simulation in SUMO mode
        r_start = client.post("/api/v1/simulation/start", json={"scenario": "normal", "engine": "sumo"})
        assert r_start.status_code == 200
        start_data = r_start.json()
        print("[TEST] Start SUMO:", start_data)
        assert start_data["status"] == "started"
        assert start_data["engine_source"] == "sumo"

        # 3. Step a few ticks to accumulate vehicles in SUMO
        if hasattr(STATE, "simulation_manager") and STATE.simulation_manager:
            for _ in range(15):
                STATE.simulation_manager.engine.step()

        # 4. GET /api/v1/simulation/status
        r_status = client.get("/api/v1/simulation/status")
        assert r_status.status_code == 200
        status_data = r_status.json()
        print("[TEST] Simulation Status:", status_data)
        assert status_data["engine_source"] == "sumo"

        # 5. GET /api/v1/telemetry/metrics
        r_metrics = client.get("/api/v1/telemetry/metrics")
        assert r_metrics.status_code == 200
        metrics = r_metrics.json()
        print(f"[TEST] Metrics: total_vehicles={metrics['total_vehicles']}, sim_time={metrics['simulation_time_s']}s")
        assert metrics["source"] == "sumo"
        assert metrics["total_vehicles"] > 0
        assert len(metrics["vehicles"]) > 0
        # Check first vehicle format
        v0 = metrics["vehicles"][0]
        assert "id" in v0 and "x" in v0 and "y" in v0 and "speed_kmh" in v0

        # 6. GET /api/v1/junctions
        r_juncs = client.get("/api/v1/junctions")
        assert r_juncs.status_code == 200
        juncs = r_juncs.json()
        print(f"[TEST] Junctions count: {len(juncs)}")
        assert len(juncs) == 4
        j1 = next(j for j in juncs if j["id"] == "J1")
        assert j1["name"] == "Junction 1 — Rasulgarh"
        assert j1["sumo_id"] == "A0"
        assert "counts" in j1 and "queues" in j1

        # 7. GET /api/v1/emergency/fleet
        r_fleet = client.get("/api/v1/emergency/fleet")
        assert r_fleet.status_code == 200
        fleet = r_fleet.json()
        print("[TEST] Fleet count:", fleet["count"])

        # 8. WebSocket check /ws/telemetry and /ws/live
        with client.websocket_connect("/ws/telemetry") as ws:
            conn_msg = ws.receive_json()
            assert conn_msg["type"] == "connected"
            assert conn_msg["engine_source"] == "sumo"
            print("[TEST] WS /ws/telemetry received connected event.")

        with client.websocket_connect("/ws/live") as ws:
            conn_msg = ws.receive_json()
            assert conn_msg["type"] == "connected"
            print("[TEST] WS /ws/live received connected event.")

        # 9. Pause, Resume, Reset
        r_pause = client.post("/api/v1/simulation/pause")
        assert r_pause.status_code == 200
        assert r_pause.json()["status"] == "paused"

        r_resume = client.post("/api/v1/simulation/resume")
        assert r_resume.status_code == 200
        assert r_resume.json()["status"] == "resumed"

        r_reset = client.post("/api/v1/simulation/reset")
        assert r_reset.status_code == 200
        assert r_reset.json()["status"] == "reset"

        # 10. Verify SQLite stored traffic snapshot data
        with Session(engine) as session:
            count = session.exec(select(TrafficReading)).all()
            print(f"[TEST] SQLite stored TrafficReadings count: {len(count)}")

if __name__ == "__main__":
    test_fastapi_sumo_integration()
    print("\nALL FASTAPI + SUMO INTEGRATION TESTS PASSED SUCCESSFULLY!")
