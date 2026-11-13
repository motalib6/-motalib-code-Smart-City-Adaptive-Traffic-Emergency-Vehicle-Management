# RUNNING SMARTFLOW ODISHA

## Quick Start (One-Click)
Double-click `smartflow-odisha\start-smartflow.bat` from the repository root.

---

## Manual Startup Commands

### 1. Start the FastAPI Backend
Open a terminal (PowerShell or Command Prompt):
```powershell
cd "smartflow-odisha\backend"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
- API Docs: `http://127.0.0.1:8000/docs`
- Health Check: `http://127.0.0.1:8000/health`

### 2. Start the Frontend
Open a second terminal:
```powershell
cd "smartflow-odisha\frontend"
npm run dev
```
- Open browser at: `http://localhost:5173`

### 3. Default Login Credentials
- **Email:** `admin@smartflow.local`
- **Password:** `ChangeMe123!`

---

## Recovery & Troubleshooting

### TraCI Connection In Use
If SUMO terminated unexpectedly and TraCI reports `Connection 'default' is already active`:
```powershell
taskkill /F /IM sumo.exe
taskkill /F /IM sumo-gui.exe
```
Then restart the backend.

### Reset Database
To clear data and re-seed from scratch:
```powershell
Remove-Item "smartflow-odisha\backend\data\smartflow.db"
```
The backend automatically recreates and re-seeds tables on next startup.
