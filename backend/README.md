# SMARTFLOW ODISHA — Backend

FastAPI + SQLModel (SQLite) backend for the GEC Hackathon 2026 PS-03 prototype.
No paid APIs. SUMO and YOLO are optional — the backend runs fully without
them and says so in every response.

## Quick start

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate   # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m app.seed        # seeds admin@smartflow.local / ChangeMe123! (change after login)
uvicorn app.main:app --reload --port 8000
```

- Health: `GET http://127.0.0.1:8000/api/health`
- Swagger: `http://127.0.0.1:8000/docs`
- Frontend (separate): `http://localhost:5173` (CORS allowed)

## What runs without extra installs

- **SimulatedEngine** (default, `source: "simulated"`): deterministic seeded
  in-process traffic for J1–J4, scenarios normal/medium/rush/heavy/unbalanced/emergency.
- Adaptive signal engine: `D = 0.5*queue + 0.3*count + 0.2*wait`,
  `G = clip(Gmin + k*D, Gmin, Gmax)` with starvation prevention.
- Safety: NS/EW conflict matrix + state machine
  `GREEN_NS → YELLOW_NS → ALL_RED → GREEN_EW → YELLOW_EW → ALL_RED → GREEN_NS`.
  Yellow/all-red are never skipped, including for emergency priority.
- Emergency: route validation, simulated GPS (labelled as such), safe priority
  walk, next-junction preparation, event log.
- Roles: ADMIN / OPERATOR / VIEWER (Argon2 + JWT). Seeded admin:
  `admin@smartflow.local` / `ChangeMe123!` — change it after first login.

## BLOCKED / not installed in this VM

- **SUMO**: not installed (`sumo`: command not found). `SumoEngine` reports
  `available: false`; `POST /api/simulation/start` with `engine:"sumo"` → 503.
  Network/route files exist under `../simulation/sumo/` (authored, not yet
  validated with netconvert — see `simulation/sumo/README.md`).
- **YOLOv8**: `ultralytics` / `opencv-python` not installed. Vision endpoints
  report `available: false` with the exact reason; no fake detections.
  To enable: uncomment the optional lines in `requirements.txt`, then
  `pip install -r requirements.txt` (downloads torch + `yolov8n.pt`).
  COCO YOLO has **no ambulance class** — ambulance priority uses the
  separate emergency/GPS module, never vision.

## Endpoints (all under /api)

| Method | Path | Role |
|---|---|---|
| GET | /api/health | public |
| POST /api/auth/login, GET /api/auth/me | | any authed |
| GET /api/dashboard/summary | | VIEWER+ |
| GET /api/junctions, GET /api/junctions/{id} | | VIEWER+ |
| POST /api/simulation/start\|pause\|reset\|scenario, GET /api/simulation/status | | OPERATOR+ |
| POST /api/traffic/inject, GET /api/traffic/current | | OPERATOR+ / VIEWER+ |
| POST /api/vision/upload\|start\|stop, GET /api/vision/stream\|status | | OPERATOR+ |
| POST /api/emergencies, GET /api/emergencies, POST /api/emergencies/{id}/location\|complete | | OPERATOR+ |
| GET /api/events, GET /api/analytics/summary\|comparison | | VIEWER+ |
| GET/PUT /api/admin/settings, GET /api/admin/users | | ADMIN |
| WS | /ws/live | — |

## Tests

```bash
pytest -q
```

Covers density/timing bounds/starvation, conflict prevention, phase sequence,
auth RBAC (viewer cannot edit settings, unauthenticated blocked), emergency
safe transition, and the fixed-vs-adaptive comparison returning `planned`
(no invented numbers) until real runs exist.

## Layout

```
app/main.py app/config.py app/database.py app/state.py app/schemas.py app/seed.py
app/api/          auth dashboard junctions traffic simulation vision emergencies analytics events admin
app/models/       user junction signal vehicle traffic_reading emergency event simulation_run
app/services/     traffic_service signal_service emergency_service analytics_service event_service
app/safety/       conflict_matrix signal_state_machine
app/simulation/   engine_interface sumo_engine simulated_engine
app/vision/       detector video_manager lane_roi
app/websocket/    manager
app/core/         security permissions
tests/            conftest test_signal_engine test_safety test_api
data/             smartflow.db (created on startup), settings.json, uploads/
```
