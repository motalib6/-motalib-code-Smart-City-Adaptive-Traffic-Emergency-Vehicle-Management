# SUMO — deferred, remind after the main build completes

Decision by user on 2026-11-12 ~07:38 IST: SUMO baad me karna hai.
Jab frontend + backend build complete ho jaye, user ko SUMO ka reminder dena hai.

## What is pending (SUMO)

- Install Eclipse SUMO on the user's Windows PC (SUMO is NOT installed in this
  Linux VM — `sumo: command not found`, verified 2026-11-12).
- Verify `sumo --version` and `sumo-gui --version`, add SUMO `bin` to PATH if needed.
- Generate/run the 2x2 network J1–J4 (files under `simulation/sumo/`).
- Verify via TraCI: vehicles actually move, counts/queues change with scenario,
  signal states readable, adaptive green changes timing.
- Only then mark SUMO checklist items PASS. The in-process SimulatedEngine is
  NOT SUMO and must never be reported as a SUMO test pass.

## Reminder trigger

When the backend pytest + frontend `npm run build` + GitHub push are all done
and reported to the user, remind in the same message:
"SUMO ab baaki hai — Windows pe SUMO install karke TraCI verification karna hai."
