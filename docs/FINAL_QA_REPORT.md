# FINAL QA REPORT — SMARTFLOW ODISHA (verified 2026-11-12, this VM)

## TEST A — Application
| Test | Result | Evidence |
|---|---|---|
| Frontend starts (`vite`, :5173) | PASS | HTTP 200, title SMARTFLOW ODISHA |
| Frontend `npm run build` | PASS | built in 2.04s (chunk-size warning only) |
| Backend starts (`uvicorn`, :8000) | PASS | `/api/health` 200 `{"status":"ok",...}` |
| SQLite initializes | PASS | `data/smartflow.db`, tables created, events persisted |
| API health | PASS | see above |
| Authentication | PASS | login `admin@smartflow.local` returns JWT; dashboard without token → 401 |
| WebSocket connects | **PASS** | Real client test 2026-11-12: `simulation_tick` tick=967, 98 vehicles, J1–J4; script `backend/scripts/ws_test.py` |

## TEST B — SUMO
| Test | Result | Evidence |
|---|---|---|
| SUMO starts | **BLOCKED** | `sumo: command not found` in this VM; `SumoEngine` reports `available:false`, start returns 503 |
| Four-junction network | NOT VERIFIED | `simulation/sumo/network/*.xml` + routes + `.sumocfg` authored, never run through netconvert |
| Vehicles move / density / queues / signals via TraCI | NOT VERIFIED | TraCI code present in `sumo_engine.py`; needs a SUMO machine |
| Simulated engine (same interface) | PASS | rush scenario: 119 vehicles, 4 junctions, avg wait 8.18s — labelled `source: simulated`, NOT SUMO |

## TEST C — Adaptive traffic
| Test | Result | Evidence |
|---|---|---|
| Density formula | PASS | pytest: D=17.0 for Q=10,N=20,W=30 |
| Timing bounds + starvation | PASS | pytest `test_signal_engine.py` |
| Conflict prevention + phase sequence | PASS | pytest `test_safety.py`; illegal skip raises |
| Live inject | PASS | `POST /api/traffic/inject` J1/N count 22 queue 9 → density 14.8, recommended green 21.8s |

## TEST D — Emergency
| Test | Result | Evidence |
|---|---|---|
| Request created, route valid | PASS | `POST /api/emergencies` J1→J2 → 201 `PRIORITY_GRANTED`, ETA 36.0s |
| Safe transition | PASS | `safe_transition_steps: ["YELLOW_NS","ALL_RED","GREEN_EW"]`; events YELLOW_STARTED, ALL_RED_STARTED, PRIORITY_GRANTED, NEXT_JUNCTION_PREPARED persisted |
| GPS label | PASS | `gps_source: "SIMULATED GPS"` in every response |
| Priority release after passage | NOT VERIFIED LIVE | complete endpoint exists; not exercised in this run |

## TEST E — Computer vision
| Test | Result | Evidence |
|---|---|---|
| MP4 upload | PASS (endpoint) | upload validates extension, stores locally |
| YOLOv8 loads / detections | **PASS** | Real Pexels traffic video (990 frames); 62 detections in 20 sampled frames (car 47, truck 15), mean conf 0.591; annotated frame in `screenshots/`; see update section below |

## TEST F — Frontend
| Test | Result | Evidence |
|---|---|---|
| Every page opens (build) | PASS | 9 routes compile; dev server 200 |
| Real backend info | PASS | after api.ts contract fix (login `email`, sim-start body, snake_case emergency/traffic payloads), dashboard/junctions/emergency/traffic all returned live backend data |
| Events / analytics | PASS | events listed from DB; analytics summary returned real counts (1 reading, 22 vehicles observed) |

## TEST G — Security
| Test | Result | Evidence |
|---|---|---|
| Unauthenticated blocked | PASS | 401 |
| Viewer cannot edit settings | PASS | pytest RBAC 403 |
| Passwords never exposed | PASS | Argon2 hashes only; seed password must be changed after first login |

## TEST H — Persistence
| Test | Result | Evidence |
|---|---|---|
| Events survive in SQLite | PASS | 8 events incl. emergency flow readable via `/api/events` after ticks |
| Restart persistence | **PASS** | 9 events, identical ids/types before and after backend stop/restart |

## TEST I — Performance comparison
| Test | Result | Evidence |
|---|---|---|
| Fixed vs adaptive | **COMPLETED (simulated)** | Runs 1 (fixed) + 2 (adaptive) in SQLite; `GET /api/analytics/comparison` returns real numbers — fixed wait 19.23s/thr 1729/maxq 117, adaptive wait 23.44s/thr 1655/maxq 75; adaptive did NOT win on wait/throughput (see update section) |

## Update — 2026-11-12 ~08:00 IST (gap-closure run)

### WebSocket live test — PASS
Script: `backend/scripts/ws_test.py` (real `websockets` client).
```
connected to ws://127.0.0.1:8000/ws/live
MSG: {"type": "connected", "timestamp": "2026-11-12T02:28:06.169694+00:00Z", "engine_source": "simulated"}
MSG: {"type": "simulation_tick", "timestamp": "2026-11-12T02:28:06.296720+00:00Z", "source": "simulated", "tick": 967, "total_vehicles": 98, "junctions": {"J1": {"counts": {"N": 4, "S": 9, "E": 7, "W": 6}, "queues": {"N": 3, "S": 0, "E": 3, "W": 3}, "avg_wait_s": 1870.1, "total": 26}, "J2": {...}, "J3": {...}, "J4": {...}, ...}}
PASS: simulation_tick tick=967 total_vehicles=98 junctions=['J1', 'J2', 'J3', 'J4'] source=simulated
```
Raw tick message saved at `/tmp/ws-tick.json` (temp file, not in repo).
Note: the first version of the script printed `None` values because it looked
for a `"data"` wrapper; the broadcast puts fields at top level — fixed and
re-run clean (see `scripts/ws_test.py`).

### Fixed vs adaptive — COMPLETED (simulated, NOT SUMO)
Runner: `backend/scripts/run_comparison.py`. Identical inputs: 2×2 network
J1–J4, same arrival stream, seed 42, 120 ticks, scenario "unbalanced".
Model: 1 tick = 1 s; arrivals randint(0,2)/approach/tick (+extra J1/E);
saturation discharge 3 veh/green-tick/approach; cycle GREEN→YELLOW(3s)→
ALL_RED(2s)→GREEN; fixed green 30s; adaptive green from the real
`demand_for_approach()` + StarvationTracker. Metrics computed from the run.
`GET /api/analytics/comparison` now returns `status:"completed"`:
- Fixed (run_id 1): mean_wait_s 19.23, mean_queue 18.01, throughput 1729, max_queue 117
- Adaptive (run_id 2): mean_wait_s 23.44, mean_queue 19.22, throughput 1655, max_queue 75
- Total arrived identical: 2080 both runs.
Honest result: adaptive did NOT beat fixed on mean wait/throughput in this
model — it only reduced max queue (117 → 75). Seed sensitivity (seeds 7, 123)
shows the same pattern (fixed wait ~19.0–19.2s vs adaptive ~22.2–23.2s).
Likely cause: adaptive green saturates at green_max 60s → ~130s cycles,
wasting capacity when the served queue empties. Tuning green_max/demand_k is
future work; no numbers were adjusted to favour adaptive. Full JSON:
`backend/data/comparison-2026-11-12.json`.

### Restart persistence — PASS
Events BEFORE restart: 9, ids [9..1], types [SIMULATION_STARTED,
TRAFFIC_INJECTED, NEXT_JUNCTION_PREPARED, PRIORITY_GRANTED, ALL_RED_STARTED,
YELLOW_STARTED, ROUTE_VALIDATED, EMERGENCY_REQUESTED, SIMULATION_STARTED].
Backend stopped (pid 6330 killed) and restarted (new pid 11579/11581).
Events AFTER restart: 9, identical ids [9..1] and types — all emergency/
traffic history survived in SQLite. Simulation was re-started afterwards
(rush, 100 vehicles, 4 junctions); events then totalled 11 (9 + 1
TRAFFIC_INJECTED from the YOLO test + 1 SIMULATION_STARTED).

### YOLO — PASS (real video, real detections)
Install: first attempt FAILED `OSError: [Errno 28] No space left on device`
while downloading torch 2.15.0 (539.2 MB) — pip's temp dir defaulted to /tmp
(tmpfs 512 MB). Retry with `TMPDIR=/home/hatch/workspace/.pip-tmp` and
`--no-cache-dir` SUCCEEDED. Installed: opencv-python-headless 5.0.0.93,
opencv-python 5.0.0.93, torch 2.15.0, ultralytics 8.4.211
(`requirements.txt` updated with the note about TMPDIR).
Video: REAL Pexels traffic clip, free to use — "Traffic at Urban
Intersection on Sunny Day" by JMT 35,
https://www.pexels.com/video/traffic-at-urban-intersection-on-sunny-day-34494565/
(file: https://videos.pexels.com/video-files/1393755/1393755-sd_640_360_30fps.mp4,
2.6 MB, 640×360, 30 fps, 990 frames / 33 s). Saved locally at
`backend/data/uploads/traffic-intersection-pexels-1393755.mp4`.
API flow (seeded admin token): `POST /api/vision/upload` → 201 uploaded;
`POST /api/vision/start` → running:true, detector_available:true;
polling `/api/vision/status` showed live counts, e.g.
`last_counts: {"S":{"car":1},"unknown":{"car":1,"truck":1}}`;
`/api/vision/stream` returned real detections, e.g. car conf 0.639,
truck conf 0.345; `POST /api/vision/stop` → running:false.
Direct verification (`backend/scripts/yolo_video_test.py`, 20 sampled frames,
stride 15): 62 detections — car 47, truck 15, motorcycle 0, bus 0;
mean confidence 0.591; lane counts: unknown car 36/truck 14, S car 9/truck 1,
E car 2. Full JSON: `screenshots/yolo-detection-summary.json`. Annotated
frame (visually checked — real intersection, boxes + labels):
`screenshots/yolo-detection-frame.jpg`.
Camera → density engine: `POST /api/traffic/inject` with the S-approach
sampled count (vehicle_count 10, queue_length 0, avg_wait_s 0 — queue/wait
are 0 because sampled-frame counts carry no queue/wait measurement, NOT
invented) → reading_id 2, density 3.0, congestion "free",
recommended_green_s 12.4, source "yolo".
Detection-quality notes (not hidden): (a) the same vehicle is sometimes
detected as BOTH car and truck at a near-identical box (e.g. conf 0.639 car
vs 0.345 truck) — a YOLOv8n double-class artifact; (b) most centres fall in
"unknown" lane because the default ROIs assume a four-way junction view
while this clip is a street-level view — ROIs need per-camera calibration;
(c) no motorcycle/bus appeared in this clip, so those classes are
unverified on real footage; (d) counts sum over sampled frames, so one
vehicle can be counted multiple times — they prove detection, not a
unique-vehicle census.

### PROMPT 00 docs — DONE
`docs/REQUIREMENTS.md`, `docs/TRACEABILITY_MATRIX.md`,
`docs/TECHNICAL_ARCHITECTURE.md`, `docs/IMPLEMENTATION_ORDER.md`,
`docs/API_CONTRACT.md` written from the implemented code/spec. Known gaps
recorded in them: async analytics worker not implemented, MJPEG stream
status-only, `app/models/road.py` absent, PS-03.pdf/PPTX files were never
provided so requirements derive from the pasted spec text.

## Backend pytest (verified by parent, 2026-11-12)
`25 passed, 12 warnings in 1.32s` (warnings: Starlette/httpx deprecation + test-secret key length).

## Integration bugs found & fixed during linking
1. Frontend login sent `{username}` — backend expects `{email}` → fixed in `api.ts`.
2. Frontend `simStart()` sent no body — backend requires `SimulationStartRequest` → now sends `{scenario, engine:"simulated"}`.
3. Frontend emergency/traffic payloads used camelCase — backend uses snake_case → mapped in `api.ts`.
