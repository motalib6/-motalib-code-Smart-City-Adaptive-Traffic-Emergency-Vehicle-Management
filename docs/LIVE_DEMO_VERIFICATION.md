# LIVE DEMO VERIFICATION REPORT
**Project:** SMARTFLOW ODISHA (PS-03)  
**Execution Timestamp:** 2026-11-12T18:20:00+05:30  
**Platform:** Windows 10/11 x64, Python 3.11.9, Node.js v24.15.0, Eclipse SUMO 1.28.0  

---

## 1. Verification Matrix & Results

| Test Phase | Status | Verification Summary & Evidence |
|---|---|---|
| **Phase 1: Project Path Audit** | **PASS** | `smartflow.sumocfg` resolves reliably across relative and absolute paths (`backend/`, `smartflow-odisha/`, and root). |
| **Phase 2: Security & Credentials** | **PASS** | `.env` and `.db` gitignored. Added `POST /api/auth/change-password` endpoint. Default seed password is dev-only. |
| **Phase 3: Backend Launch** | **PASS** | Single Uvicorn process listening on `127.0.0.1:8000`. `/health` and `/docs` return 200 OK. |
| **Phase 4: SUMO Live Test** | **PASS** | Single SUMO process started via `SimulationManager`. TraCI tracked 6 active vehicles moving through J1–J4. |
| **Phase 5: Full Frontend Test** | **PASS** | `npm run build` completed with zero TypeScript errors. WebSocket connected on `/ws/telemetry`. |
| **Phase 6: Emergency Demonstration** | **PASS** | Real `AMB-01` emergency priority tested. Verified signal sequence: `YELLOW_STARTED` -> `ALL_RED_STARTED` -> `PRIORITY_GRANTED` -> `PRIORITY_RELEASED` -> `NEXT_JUNCTION_PREPARED`. |
| **Phase 7: Startup Script** | **PASS** | `start-smartflow.bat` updated with pre-flight checks, automatic health poll loop, and browser launch. |

---

## 2. Tested Signal Sequence Details
The emergency corridor preemption follows a safe clearance progression:
1. `YELLOW_STARTED`: 3.0s clearance initiated for conflicting approaches.
2. `ALL_RED_STARTED`: 2.0s all-red intersection clearance before switching.
3. `PRIORITY_GRANTED`: Green light assigned along ambulance approach corridor.
4. `PRIORITY_RELEASED`: Priority released immediately when vehicle clears detector loop.
5. `NEXT_JUNCTION_PREPARED`: Advance green triggered for next junction in route.

---

## 3. Launching Live Application

### One-Click Launch:
```powershell
.\start-smartflow.bat
```

### Manual Launch:
**Terminal 1 (Backend):**
```powershell
cd "smartflow-odisha\backend"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

**Terminal 2 (Frontend):**
```powershell
cd "smartflow-odisha\frontend"
npm run dev
```
