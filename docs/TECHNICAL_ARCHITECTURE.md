# TECHNICAL ARCHITECTURE — SMARTFLOW ODISHA

## Data flow

```
React + TypeScript (Vite, :5173)
  │  REST /api  +  WebSocket /ws/live
  ▼
FastAPI (Python, :8000) — app/main.py, lifespan seeds junctions + admin
  ├─ api/          auth, dashboard, junctions, traffic, simulation,
  │                vision, emergencies, analytics, events, admin
  ├─ services/     traffic (density), signal (adaptive green + starvation),
  │                emergency (route/ETA), analytics (summary + comparison),
  │                event (persistent logging)
  ├─ safety/       conflict_matrix (NS vs EW exclusive),
  │                signal_state_machine (GREEN→YELLOW→ALL_RED→GREEN)
  ├─ simulation/   engine_interface, sumo_engine (TraCI, real SUMO when
  │                installed), simulated_engine (seeded, labelled simulated)
  ├─ vision/       detector (lazy YOLOv8n), video_manager (MP4/webcam),
  │                lane_roi (N/S/E/W polygons)
  ├─ websocket/    manager (broadcast simulation_tick 1×/s while running)
  └─ core/         security (Argon2 + JWT), permissions (role checks)
  ▼
SQLite (backend/data/smartflow.db, SQLModel) — users, junctions, signals,
traffic readings, vehicle observations, emergencies, events, simulation runs
```

## Two input modes (per spec)

- **Mode A — SUMO sensor data:** `SumoEngine` via TraCI. BLOCKED in this VM
  (SUMO not installed); the API reports `sumo_available: false` and a 503
  with the exact reason instead of faking it.
- **Mode B — YOLO camera data:** local MP4/webcam → OpenCV → YOLOv8n →
  lane ROIs → aggregated counts → `POST /api/traffic/inject` → the same
  adaptive engine. Camera failure never breaks Mode A.

## Signal control (the algorithm)

- Density per approach: `D = 0.5·queue + 0.3·count + 0.2·avg_wait_s`
  (weights configurable in admin settings).
- Green: `G = clip(Gmin + k·D, Gmin, Gmax)`, defaults Gmin 10s, Gmax 60s, k 0.8.
- Starvation: `StarvationTracker` forces service after 6 ticks unserved.
- Phase groups: NS and EW, mutually exclusive by conflict matrix.
- Every transition is validated by the state machine; yellow (default 3s)
  and all-red (default 2s) are mandatory, including emergency priority.

## Emergency flow

`POST /api/emergencies` → route validation (adjacency, known junctions) →
`ROUTE_VALIDATED` → current green terminated via state machine
(`YELLOW_STARTED` → `ALL_RED_STARTED`) → `PRIORITY_GRANTED` →
`NEXT_JUNCTION_PREPARED` (ETA-based) → GPS updates via
`POST /api/emergencies/{id}/location` (SIMULATED GPS) →
`POST /api/emergencies/{id}/complete` → `PRIORITY_RELEASED` +
`EMERGENCY_COMPLETED`. Invalid route / unknown junction → 422.

## Synchronous vs asynchronous (PROMPT 12)

- Synchronous (never deferred): conflict validation, state transitions,
  yellow/all-red clearance, emergency safety decisions, config validation.
  These run inline in the request path.
- Asynchronous: NOT implemented as a separate worker in this build — there
  is no asyncio.Queue/Redis/Kafka. Historical analytics, CSV export and
  summaries run synchronously in their request handlers. This is a known
  gap, recorded honestly; adding a lightweight asyncio.Queue worker is
  future work and must not block signal safety.

## Configuration

- `backend/.env.example` (JWT secret, CORS origins, signal defaults).
  Admin settings persist to `backend/data/settings.json`.
- Frontend: `VITE_API_BASE_URL=http://127.0.0.1:8000`,
  `VITE_WS_URL=ws://127.0.0.1:8000/ws/live` (see `frontend/.env.example`).
- Seed admin: `admin@smartflow.local` / `ChangeMe123!` — change after first login.
