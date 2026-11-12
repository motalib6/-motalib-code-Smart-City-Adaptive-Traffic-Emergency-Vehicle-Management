# REQUIREMENTS — SMARTFLOW ODISHA (PROMPT 00 output)

Source: PS-03 (mandatory acceptance requirements) + SMARTFLOW-SOLUTION PPT
(our proposed solution / USP). This file was written after the implementation
existed; every requirement below maps to a built module — see
TRACEABILITY_MATRIX.md. Nothing in this file invents a feature that is not
in PS-03, the PPT, or the implemented code.

## 1. Mandatory PS-03 requirements

| ID | Requirement | Status (2026-11-12) |
|----|-------------|---------------------|
| M1 | Road and junction representation (4 junctions, N/S/E/W approaches) | Implemented — J1–J4, `app/models/junction.py`, `simulation/sumo/network/` |
| M2 | Traffic signal representation (phases, countdown) | Implemented — `app/safety/signal_state_machine.py` |
| M3 | Traffic density inputs (counts, queues, waiting time) | Implemented — `POST /api/traffic/inject`, `GET /api/traffic/current` |
| M4 | Adaptive signal timings from density | Implemented — `D = 0.5Q + 0.3N + 0.2W`, `G = clip(Gmin + kD, Gmin, Gmax)` |
| M5 | Emergency vehicle priority | Implemented — `POST /api/emergencies` + safe priority walk |
| M6 | Safe signal transitions (yellow + all-red never skipped) | Implemented — conflict matrix + state machine; pytest-verified |
| M7 | Congestion monitoring | Implemented — density score → free/moderate/congested/severe |
| M8 | Event logs and analytics (persistent) | Implemented — SQLite `Event` table, `GET /api/events`, analytics summary |
| M9 | Authorized administrative operations (roles) | Implemented — ADMIN/OPERATOR/VIEWER, Argon2 + JWT, RBAC tests |
| M10 | Connected simulation dashboard (live) | Implemented — React dashboard + WebSocket `/ws/live` |

## 2. PPT solution / USP requirements

| ID | Requirement | Status (2026-11-12) |
|----|-------------|---------------------|
| U1 | YOLOv8 vehicle detection from local video/webcam | Code implemented (`app/vision/`); live verification IN PROGRESS — ultralytics/opencv install running, real Pexels traffic video downloaded; see FINAL_QA_REPORT.md |
| U2 | Emergency vehicle GPS/route tracking | Implemented — SIMULATED GPS, labelled as such in every response |
| U3 | AI-based adaptive traffic signal engine | Implemented (see M4) |
| U4 | Predictive emergency priority (next-junction preparation) | Implemented — `NEXT_JUNCTION_PREPARED` event, ETA-based |
| U5 | Yellow and all-red safety transitions | Implemented (see M6) |
| U6 | Connected junction coordination (J1 → J2 → J3/J4) | Implemented in simulated engine + emergency service; SUMO verification BLOCKED |
| U7 | Live traffic dashboard | Implemented — 8 screens, 9 routes |
| U8 | SUMO simulation (2×2 network, TraCI control) | Code + network files implemented; live run BLOCKED — SUMO not installed in this VM |

## 3. Non-functional requirements

- N1 Free/open-source stack only; no paid API key. Met: FastAPI, React, SQLite, SUMO, YOLOv8n.
- N2 No real-world signal hardware control. Met: simulation only.
- N3 No invented performance numbers. Met: comparison returns `planned` until real runs exist; 2026-11-12 comparison runs are computed (see FINAL_QA_REPORT.md).
- N4 Sample/demo data labelled. Met: frontend DEMO DATA banner when backend unreachable.
- N5 COCO YOLO has no ambulance class — ambulance priority must use the separate emergency module. Met: detector only reports car/motorcycle/bus/truck.

## 4. Unsupported assumptions / missing external data

- A1 No real traffic-camera feed exists; vision input is a local MP4 or webcam.
- A2 No real ambulance GPS feed exists; GPS is simulated along routes.
- A3 PS-03.pdf and SMARTFLOW-SOLUTION.pptx were NOT provided as files in this workspace; requirements above are taken from the user's pasted spec text (the same text that drove the implementation). If the actual PDF/PPTX differ, this file must be re-checked against them.
- A4 SUMO verification needs a Windows machine with Eclipse SUMO installed (see SUMO_LATER.md).
- A5 Fixed-vs-adaptive numbers come from a documented queue model on the simulated engine, not from SUMO/TraCI measurements (see backend/scripts/run_comparison.py).
