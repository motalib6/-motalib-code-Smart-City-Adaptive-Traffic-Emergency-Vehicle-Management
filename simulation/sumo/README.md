# SUMO — status note (2026-11-12)

## What exists
- `network/smartflow.nod.xml` — 2×2 junction grid J1–J4 + 8 boundary nodes.
- `network/smartflow.edg.xml` — 24 directed edges, 2 lanes, 50 km/h.
- `routes/smartflow.rou.xml` — vTypes car / motorcycle / bus / truck / ambulance,
  through + turning routes, normal-scenario flows, one demo ambulance vehicle.
- `config/smartflow.sumocfg` — SUMO run config (1 s step, 3600 s).
- `build_network.py` — runs `netconvert` to produce `smartflow.net.xml`.

## What is NOT verified — do not claim a SUMO PASS
- **SUMO is NOT installed in this VM** (`sumo`: command not found, checked
  2026-11-12). `netconvert` / `sumo-gui` have therefore never run here.
- The network files are authored, not generated/validated. On a machine with
  SUMO installed, run `python simulation/sumo/build_network.py`, then
  `sumo-gui -c simulation/sumo/config/smartflow.sumocfg` and confirm
  vehicles move at J1–J4 before using the SUMO engine.
- Until then the backend uses `SimulatedEngine` (source label `"simulated"`
  in every API response) and `SumoEngine.status()` reports
  `available: false` with the exact reason. `POST /api/simulation/start`
  with `engine: "sumo"` returns HTTP 503 with that reason.
