# SMARTFLOW — 22-point checklist (verified 2026-11-12, this VM; updated ~08:00 IST)

## DONE — verified live
1. PS-03/PPT requirements extracted — DONE 2026-11-12: `docs/REQUIREMENTS.md`,
   `TRACEABILITY_MATRIX.md`, `TECHNICAL_ARCHITECTURE.md`,
   `IMPLEMENTATION_ORDER.md`, `API_CONTRACT.md`. (Caveat: PS-03.pdf/PPTX files
   were never provided; requirements derive from the pasted spec text.)
2. Stitch 8 screens — DONE as React (Stitch export itself needs user's Google sign-in).
3. Stitch UI imported into Antigravity — NOT DONE (no Antigravity/Stitch export exists).
4. React frontend builds — PASS (`npm run build` 2.04s; re-run pending at end of gap-closure).
5. FastAPI backend runs — PASS (`/api/health` 200).
6. SQLite records persist — PASS (events readable via API).
7. SUMO 4-junction network runs — BLOCKED (SUMO not installed here).
8. Vehicles move in actual SUMO — BLOCKED (same).
9. Traffic density measured — PASS (inject → density 14.8, green 21.8s).
10. Adaptive signal timings — PASS (pytest + live).
11. Yellow + all-red transitions — PASS (pytest + live emergency walk).
12. Signal conflict tests — PASS (pytest 25 passed).
13. Ambulance request + GPS simulator — PASS (PRIORITY_GRANTED, SIMULATED GPS, ETA 36s).
14. Emergency priority in SUMO — BLOCKED (needs SUMO).
15. J1→J2 coordination — PARTIAL: NEXT_JUNCTION_PREPARED event in simulated engine; not in SUMO.
16. YOLO detects vehicles in actual video — PASS 2026-11-12: installed
    opencv 5.0.0.93, torch 2.15.0, ultralytics 8.4.211; real Pexels video
    (990 frames); 62 detections in 20 sampled frames (car 47, truck 15),
    mean conf 0.591; annotated frame + summary JSON in `screenshots/`.
    Caveats: car/truck double-detection artifact; most centres "unknown"
    lane (ROIs need per-camera calibration); no motorcycle/bus in this clip.
17. Camera density reaches adaptive controller — PASS: YOLO S-approach count
    injected → density 3.0, recommended green 12.4s, source "yolo"
    (reading_id 2; queue/wait 0, not invented).
18. WebSocket updates UI — PASS (live client test 2026-11-12):
    `simulation_tick` tick=967, 98 vehicles, J1–J4, source=simulated.
    Script: `backend/scripts/ws_test.py`.
19. Auth + roles — PASS (401/403 pytest + live login).
20. Event history + analytics persist — PASS incl. restart: 9 events,
    identical ids/types before and after backend stop/restart.
21. Fixed vs adaptive test — DONE 2026-11-12 (simulated queue model, NOT SUMO):
    `backend/scripts/run_comparison.py`, seed 42, 120 ticks, unbalanced.
    Fixed run 1: wait 19.23s, queue 18.01, throughput 1729, max queue 117.
    Adaptive run 2: wait 23.44s, queue 19.22, throughput 1655, max queue 75.
    Adaptive did NOT beat fixed on wait/throughput — reported as computed.
    `GET /api/analytics/comparison` now returns `status:"completed"`.
22. Final demo + PPT evidence — PARTIAL: YOLO annotated frame + summary JSON
    DONE (`screenshots/`); dashboard/live-map screenshots not yet captured;
    PPT update needs the actual PPT file (never provided).

## Remaining gaps, in priority order
1. GitHub push — blocked on Muse GitHub App install for the repo (out of scope for this task).
2. SUMO on Windows — install + netconvert + TraCI verification (stays BLOCKED here).
3. Adaptive tuning investigation (green_max/demand_k) — comparison shows adaptive losing on wait/throughput.
4. Async analytics worker (PROMPT 12) — not implemented; analytics run synchronously.
5. MJPEG vision stream — status-only, not implemented.
6. YOLO follow-ups: per-camera ROI calibration; a clip containing
   motorcycle/bus for those classes; NMS/double-class handling.

## Final verification (gap-closure run, 2026-11-12)
- `backend/.venv/bin/python -m pytest -q` → **25 passed, 12 warnings in 1.36s**
- `cd frontend && npm run build` → **PASS, built in 2.66s**
- Backend :8000 + frontend :5173 left RUNNING; simulation re-started (rush, 100 vehicles, 4 junctions).
