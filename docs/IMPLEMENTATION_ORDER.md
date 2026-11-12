# IMPLEMENTATION ORDER — SMARTFLOW ODISHA

Build order actually followed (and what remains):

1. ✅ Scaffold + requirements (docs/REQUIREMENTS.md, TRACEABILITY_MATRIX.md,
   this file, API_CONTRACT.md) — written from the implemented spec.
2. ✅ Backend core: FastAPI, SQLite/SQLModel, auth (Argon2 + JWT), roles.
3. ✅ Safety: conflict matrix + signal state machine (with pytest).
4. ✅ Adaptive engine: density + green formula + starvation tracker.
5. ✅ Simulation: `SimulatedEngine` (seeded) + `SumoEngine` (TraCI code);
   SUMO network/routes/config files authored.
6. ✅ Emergency: request → safe priority walk → GPS simulator → completion.
7. ✅ Frontend: 9 routes / 8 screens, typed API + WebSocket clients.
8. ✅ Full-stack integration: contract mismatches found live and fixed
   (login `email`, sim-start body, snake_case emergency/traffic payloads).
9. ✅ Verification: pytest 25 passed, `npm run build` PASS, live API +
   WebSocket smoke tests.
10. 🔄 YOLO live verification (2026-11-12, in progress): install
    opencv-python-headless + ultralytics, real Pexels traffic video,
    upload/start/detections/inject — see FINAL_QA_REPORT.md.
11. ✅ Fixed-vs-adaptive comparison (2026-11-12): `backend/scripts/run_comparison.py`,
    simulated queue model, seed 42, 120 ticks, scenario unbalanced.
    Runs 1 (fixed) and 2 (adaptive) in SQLite.
12. ⏳ Remaining (not done, in priority order):
    a. GitHub push — blocked on Muse GitHub App install for the repo.
    b. SUMO on a Windows machine: install Eclipse SUMO, run
       `simulation/sumo/build_network.py`, verify TraCI (counts, phases,
       moving vehicles), then re-run the comparison against SUMO data.
    c. YOLO tuning + MJPEG stream (currently status-only).
    d. Async analytics worker (asyncio.Queue) per PROMPT 12.
    e. Screenshots + PPT update (needs the actual PPT/PS-03 files).
    f. Adaptive tuning: the 2026-11-12 comparison shows adaptive losing on
       mean wait/throughput (green saturating at 60s → long cycles);
       investigate green_max / demand_k before claiming any improvement.
