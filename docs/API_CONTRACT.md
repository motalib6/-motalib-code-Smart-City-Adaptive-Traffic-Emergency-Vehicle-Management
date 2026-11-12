# API CONTRACT — SMARTFLOW ODISHA (as implemented, 2026-11-12)

Base: `http://127.0.0.1:8000` · Docs: `/docs` · All `/api/*` except
`/api/health` require `Authorization: Bearer <JWT>` (401 without token).
Error shape: `{"detail": "..."}`. Roles: ADMIN / OPERATOR / VIEWER.

## Health & auth

| Method & path | Auth | Request | Response |
|---|---|---|---|
| `GET /api/health` | none | — | `{status:"ok", app, version, engine_source, sumo_available, sumo_detail, simulation_running}` |
| `POST /api/auth/login` | none | `{email, password}` | `{access_token, token_type:"bearer", role, email}` — 401 invalid credentials |
| `GET /api/auth/me` | any role | — | `{id, email, role, is_active}` |

## Dashboard / junctions

| Method & path | Auth | Response |
|---|---|---|
| `GET /api/dashboard/summary` | any | `{source, simulation_running, scenario, tick, total_vehicles, active_junctions, avg_wait_s, active_emergencies, emergency, phases, junctions, analytics, settings}` |
| `GET /api/junctions` | any | `[{id, name, x, y, lanes, phase, live:{counts,queues,avg_wait_s,total}, source}]` |
| `GET /api/junctions/{id}` | any | `{id, name, x, y, phase, live, demand:{N/S/E/W:{density, green_s}}, explanation, source}` — 404 unknown junction |

## Simulation

| Method & path | Auth | Request | Response |
|---|---|---|---|
| `GET /api/simulation/status` | any | — | engine status + `{sumo_available, sumo_detail, engine_source}` |
| `POST /api/simulation/start` | ADMIN/OPERATOR | `{scenario:"normal" (default), engine:"simulated" (default) \| "sumo"}` | `{status:"started", engine_source, ...engine.status()}` — 503 if engine=sumo and SUMO missing; 422 unknown scenario |
| `POST /api/simulation/pause` | ADMIN/OPERATOR | — | `{status:"paused", ...}` |
| `POST /api/simulation/reset` | ADMIN/OPERATOR | — | `{status:"reset", ...}` |
| `POST /api/simulation/scenario` | ADMIN/OPERATOR | `{scenario}` | engine status — 422 unknown scenario |

## Traffic

| Method & path | Auth | Request | Response |
|---|---|---|---|
| `POST /api/traffic/inject` | ADMIN/OPERATOR | `{junction_id:"J1".."J4", approach:"N"\|"S"\|"E"\|"W", vehicle_count>=0, queue_length>=0 (default 0), avg_wait_s>=0 (default 0), source:"manual" (default)}` | 201 `{reading_id, junction_id, approach, density, congestion:"free"\|"moderate"\|"congested"\|"severe", recommended_green_s, source}` — 422 unknown junction |
| `GET /api/traffic/current` | any | — | `{source, simulation:<engine snapshot>, recent_readings:[...20 latest]}` |

## Vision (YOLO)

| Method & path | Auth | Request | Response |
|---|---|---|---|
| `GET /api/vision/status` | any | — | `{available, detector_available, detector_error, running, source, filename, last_counts}` |
| `POST /api/vision/upload` | ADMIN/OPERATOR | multipart `file` (.mp4/.avi/.mov/.mkv) | 201 `{status:"uploaded", filename, path, note:"Video stays local..."}` — 422 wrong extension |
| `POST /api/vision/start` | ADMIN/OPERATOR | `{source:"upload"\|"webcam", filename?, index?}` (body optional) | engine status — 503 if opencv missing; 422 if no video uploaded |
| `POST /api/vision/stop` | ADMIN/OPERATOR | — | status |
| `GET /api/vision/stream` | any | — | status-only: `{stream:"unavailable"\|"status-only", detections:[...], ...}` — no MJPEG in this build |

## Emergencies

| Method & path | Auth | Request | Response |
|---|---|---|---|
| `POST /api/emergencies` | ADMIN/OPERATOR | `{ambulance_id:"AMB-01" (default), current_junction, destination_junction, route:[] (default [current, destination]), speed_kmh:40.0 (default)}` | 201 `{id, ambulance_id, route, status:"PRIORITY_GRANTED", next_junction, eta_s, safe_transition_steps:["YELLOW_NS","ALL_RED","GREEN_EW"], gps_source:"SIMULATED GPS"}` — 422 invalid route |
| `GET /api/emergencies` | any | — | `[{id, ambulance_id, route, current_junction, destination_junction, status, progress, eta_s, created_at}]` (latest 50) |
| `POST /api/emergencies/{id}/location` | ADMIN/OPERATOR | `{junction_id?, x?, y?, speed_kmh?, progress?}` | `{id, current_junction, next_junction, eta_s, progress, gps_source:"SIMULATED GPS"}` — 404 unknown id; 422 completed / junction not on route |
| `POST /api/emergencies/{id}/complete` | ADMIN/OPERATOR | — | `{id, status:"COMPLETED"}` — logs PRIORITY_RELEASED + EMERGENCY_COMPLETED |

## Analytics / events / admin

| Method & path | Auth | Response |
|---|---|---|
| `GET /api/analytics/summary` | any | `{readings, total_vehicles_observed, mean_wait_s, max_queue, events, emergency_events}` |
| `GET /api/analytics/comparison` | any | `{status:"completed", fixed:{run_id, mean_wait_s, mean_queue, throughput, max_queue}, adaptive:{...}, note}` or `{status:"planned", message, fixed:null, adaptive:null}` |
| `GET /api/events?type=&junction_id=&limit=100` | any | `[{id, type, junction_id, message, source, created_at}]` newest first, max 500 |
| `GET /api/admin/settings` | ADMIN | current settings dict |
| `PUT /api/admin/settings` | ADMIN | `{green_min_s?, green_max_s?, yellow_s?, all_red_s?, demand_k?, w_queue?, w_count?, w_wait?, scenario?}` — 422 if green_min >= green_max; returns updated settings |
| `GET /api/admin/users` | ADMIN | `[{id, email, role, is_active}]` |

## WebSocket

`WS /ws/live` — no auth token in this build (known limitation; see
TECHNICAL_ARCHITECTURE.md). Server broadcasts:
`{type:"connected", timestamp, engine_source}` on connect, then while the
simulation runs, 1×/s:
`{type:"simulation_tick", timestamp, source, tick, total_vehicles,
junctions:{J1..J4:{counts,queues,avg_wait_s,total}}, phases, emergency}`.
Client should send periodic text (ping) to keep the connection alive.

## Frontend contract notes (verified live 2026-11-12)

- Login body is `{email, password}` (the form field is labelled username).
- Sim start requires a JSON body `{scenario, engine}`.
- Emergency/traffic payloads use snake_case (frontend maps from camelCase).
