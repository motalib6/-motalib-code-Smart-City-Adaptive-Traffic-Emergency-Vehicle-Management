# SUMO BACKEND INTEGRATION REPORT
**Project:** SMARTFLOW ODISHA  
**Platform:** Windows 10/11 x64, Python 3.11.9, FastAPI 0.162.5  
**SUMO Version:** Eclipse SUMO 1.28.0  
**Date:** 2026-11-12  

---

## 1. Architecture Overview
The integration between Eclipse SUMO and SMARTFLOW ODISHA uses a dedicated `SimulationManager` that acts as the single thread-safe owner of the active TraCI session:
- **No Concurrent TraCI Conflicts:** All simulation commands (`start`, `pause`, `resume`, `stop`, `reset`) route through an async queue processed by a background worker task.
- **Headless & GUI Modes:** Headless (`sumo.exe`) by default for automated tests and high performance, with complete support for `sumo-gui.exe` when visual rendering is desired.
- **Real SUMO Telemetry:** Live extraction of vehicle positions, speeds, lane queues, waiting times, and traffic-light phases directly from TraCI.
- **Safety Preemption:** The `EmergencyPriorityManager` tracks ambulances, enforces yellow clearance, all-red clearance, and corridor green wave before restoring baseline signals.

---

## 2. Integrated Modules & Roles

| Module | Role |
|---|---|
| `app/simulation/simulation_manager.py` | Single TraCI session coordinator, async command queue, worker loop. |
| `app/simulation/sumo_engine.py` | Implementation of `SimulationEngine` driving `traci.simulationStep()` and TLS phases. |
| `app/simulation/telemetry_collector.py` | Queries vehicles (`getIDList`, `getPosition`, `getSpeed`), lane queues, and TLS states. |
| `app/simulation/emergency_priority_manager.py` | Ambulance tracking, NEMA-compliant safe transitions (YELLOW -> ALL-RED -> GREEN). |
| `app/simulation/junction_mapper.py` | Maps Bhubaneswar junctions (J1-J4) to SUMO network node IDs (`A0`, `A1`, `B0`, `B1`). |
| `app/api/v1.py` | REST endpoints for telemetry metrics, junction state, emergency fleet, and simulation controls. |
| `app/websocket/manager.py` | Real-time broadcasting to `/ws/live` and `/ws/telemetry`. |

---

## 3. Verified Endpoints & Results

All integration tests verified live (`test_fastapi_sumo.py` & `test_sumo_ambulance.py`):

1. **`GET /api/health` & `GET /health`:**
   - Detects `sumo_available: true` and `engine_source: sumo/simulated`.
2. **`POST /api/v1/simulation/start`:**
   - Body: `{"scenario": "normal", "engine": "sumo"}`
   - Result: 200 OK, spawns SUMO process with `smartflow.sumocfg`.
3. **`GET /api/v1/simulation/status`:**
   - Returns manager state, active tick, running status, scenario, and SUMO config path.
4. **`GET /api/v1/telemetry/metrics`:**
   - Returns actual vehicle count, average waiting times, total network queue, and vehicle list with positions and speeds.
5. **`GET /api/v1/junctions`:**
   - Returns real-time TLS states and approach vehicle counts for J1, J2, J3, J4.
6. **`GET /api/v1/emergency/fleet`:**
   - Returns tracked active ambulances, speed, progress, and corridor route.
7. **`WS /ws/telemetry` & `WS /ws/live`:**
   - Real-time ticks delivered to subscribers at 1 Hz with zero queue overflow.
8. **Emergency Preemption in SUMO:**
   - Real ambulance (`AMB-01`) inserted via TraCI into edge `left0A0`.
   - Yellow clearance and all-red clearance verified at junction transitions.
   - Emergency green granted along corridor and safely released after crossing.

---

## 4. Test Execution Summary

```
tests/test_fastapi_sumo.py:
  [TEST] Health: status=ok, sumo_available=True
  [TEST] Start SUMO: status=started, engine_source=sumo
  [TEST] Metrics: total_vehicles=8, sim_time=16.0s
  [TEST] Junctions count: 4
  [TEST] WS /ws/telemetry & /ws/live connected
  Status: PASSED

tests/test_sumo_ambulance.py:
  [STEP 1] Real SUMO Engine started
  [STEP 2] Inserted AMB-01 into SUMO network
  [STEP 3] Verified PREEMPTING_YELLOW, PREEMPTING_ALL_RED, GREEN_GRANTED, CLEARED
  [STEP 4] 14 safety priority events logged in SQLite
  Status: PASSED
```

Integration complete, verified, and operational.
