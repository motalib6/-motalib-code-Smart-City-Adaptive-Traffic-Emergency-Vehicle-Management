# SUMO on Windows — step-by-step (user's laptop)

Do these steps while the PWA/app work finishes. No API key needed anywhere.

## 1. Install SUMO
1. Open https://eclipse.dev/sumo/ → Downloads → Windows installer
   (file like `sumo-win64-1.22.0.msi` — version number may differ).
2. Run the installer. On the component screen keep the defaults
   (SUMO, SUMO-GUI, tools). Note the install folder, usually
   `C:\Program Files (x86)\Eclipse\SUMO`.
3. The installer normally adds SUMO to PATH. If not: search Windows for
   "Edit the system environment variables" → Environment Variables →
   Path → New → `C:\Program Files (x86)\Eclipse\SUMO\bin`
   (adjust to your actual install folder).

## 2. Verify (new PowerShell window — old ones don't see the new PATH)
```powershell
sumo --version
sumo-gui --version
netconvert --version
```
All three must print a version. If `sumo` is "not recognized", the PATH
step above is wrong — fix it and open a NEW PowerShell window.

## 3. Get the project
```powershell
git clone https://github.com/motalib6/-motalib-code-Smart-City-Adaptive-Traffic-Emergency-Vehicle-Management.git smartflow-odisha
cd smartflow-odisha
```

## 4. Build the SUMO network (first time only)
```powershell
py -m pip install sumolib traci
python simulation\sumo\build_network.py
```
This runs `netconvert` on `simulation/sumo/network/*.xml` and must
succeed with no errors. If it fails, save the exact error — do not guess.

## 5. See the cars move (SUMO-GUI)
```powershell
sumo-gui -c simulation\sumo\config\smartflow.sumocfg
```
Press Play in SUMO-GUI. You must see 4 junctions (J1–J4) with cars,
buses, motorcycles and trucks moving. Change the scenario in the
backend (see step 6) and confirm the counts change.

## 6. Run the full app with SUMO as the engine
```powershell
.\start-smartflow.bat
```
Then in a browser: http://localhost:5173 → login
`admin@smartflow.local` / `ChangeMe123!` → Live Network → Start.
The backend health endpoint must now say:
`"engine_source": "sumo", "sumo_available": true`
(check http://127.0.0.1:8000/api/health).
To switch engine, use `POST /api/simulation/start` with
`{"scenario": "rush", "engine": "sumo"}` (Swagger: /docs).
If it returns 503, SUMO is still not on PATH — go back to step 2.

## 7. What counts as PASS
- `sumo --version` prints a version
- `build_network.py` succeeds
- SUMO-GUI shows moving vehicles at J1–J4
- `/api/health` says `sumo_available: true`
- Dashboard vehicle counts change when the scenario changes
- Emergency J1→J2 still walks YELLOW → ALL_RED → GREEN

The in-process SimulatedEngine is NOT SUMO — never report it as a SUMO pass.
