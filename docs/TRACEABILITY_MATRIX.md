# TRACEABILITY MATRIX — requirement → implementation → test

| Req | Implementation | Test / evidence |
|-----|----------------|-----------------|
| M1 roads/junctions | `backend/app/models/junction.py`, `simulation/sumo/network/smartflow.{nod,edg}.xml`, `frontend/src/pages/LiveNetwork.tsx` | `GET /api/junctions` returns J1–J4 (verified live 2026-11-12) |
| M2 signals | `backend/app/safety/signal_state_machine.py`, `frontend/src/components/TrafficSignal.tsx` | pytest `test_safety.py` phase sequence + illegal-skip rejection |
| M3 density inputs | `POST /api/traffic/inject`, `GET /api/traffic/current`, `app/services/traffic_service.py` | Live inject J1/N: density 14.8, green 21.8s |
| M4 adaptive timings | `app/services/signal_service.py` (`adaptive_green`, `demand_for_approach`, `StarvationTracker`) | pytest `test_signal_engine.py`; live junction demand |
| M5 emergency priority | `app/api/emergencies.py`, `app/services/emergency_service.py` | Live: J1→J2 `PRIORITY_GRANTED`, steps YELLOW_NS → ALL_RED → GREEN_EW, ETA 36s |
| M6 safe transitions | `app/safety/conflict_matrix.py` + state machine | pytest conflict prevention; live event log YELLOW_STARTED, ALL_RED_STARTED |
| M7 congestion | `traffic_service.congestion_level` | Live inject returned `congestion: moderate` |
| M8 events/analytics | `app/models/event.py`, `app/api/events.py`, `app/services/analytics_service.py`, `frontend/src/pages/Events.tsx`, `Analytics.tsx` | `GET /api/events` 8 events pre-restart; analytics summary real counts |
| M9 roles | `app/core/security.py`, `app/core/permissions.py`, `app/api/admin.py` | pytest RBAC (401 unauthenticated, 403 viewer editing settings); live login |
| M10 live dashboard | `frontend/src/pages/Dashboard.tsx`, `app/websocket/manager.py`, `WS /ws/live` | WS test 2026-11-12: `simulation_tick` tick=967, 98 vehicles, J1–J4 (see FINAL_QA_REPORT.md) |
| U1 YOLOv8 | `app/vision/detector.py`, `video_manager.py`, `lane_roi.py`, `app/api/vision.py` | IN PROGRESS 2026-11-12: install + real Pexels video test; see FINAL_QA_REPORT.md |
| U2 emergency GPS | `app/api/emergencies.py` (`/{id}/location`), GPS simulator in emergency service | Live: `gps_source: "SIMULATED GPS"` in response |
| U3 adaptive engine | See M4 | See M4 |
| U4 predictive priority | `NEXT_JUNCTION_PREPARED` event on emergency creation | Live events list contains it |
| U5 yellow/all-red | See M6 | See M6 |
| U6 connected junctions | Emergency route J1→J2→J4 validation; simulated engine 2×2 | Simulated only; SUMO verification BLOCKED |
| U7 live dashboard | See M10 | See M10 |
| U8 SUMO | `app/simulation/sumo_engine.py` (TraCI), `simulation/sumo/` network/routes/config | BLOCKED — SUMO binary not found in this VM; `sumo_available: false`, start returns 503 |

## Gaps (no implementation)
- Fixed-vs-adaptive: implemented 2026-11-12 via `backend/scripts/run_comparison.py`
  (simulated queue model, seed 42, 120 ticks, scenario unbalanced). Result:
  fixed mean_wait 19.23s / throughput 1729 / max_queue 117;
  adaptive mean_wait 23.44s / throughput 1655 / max_queue 75.
  Adaptive did NOT beat fixed on wait/throughput in this model — reported as
  computed, not hidden. Likely cause: green saturates at 60s → ~130s cycles
  waste capacity when the served queue empties. Tuning is future work.
- Async analytics worker (asyncio.Queue, PROMPT 12): NOT implemented in this
  build — analytics run synchronously in request handlers. Documented here
  rather than claimed.
- MJPEG vision stream: NOT implemented — `GET /api/vision/stream` returns
  status-only detections, stated in the response.
- `app/models/road.py`: not present as a separate model (roads are edges in
  the SUMO network files and junction records in SQLite).
