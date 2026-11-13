@echo off
setlocal enabledelayedexpansion

REM =========================================================================
REM SMARTFLOW ODISHA — Reliable Live Launcher
REM =========================================================================

echo [SMARTFLOW] Starting pre-flight diagnostic checks...

cd /d %~dp0

REM 1. Check Python
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python not found on PATH. Please install Python 3.11+.
    pause
    exit /b 1
)

REM 2. Check SUMO Installation
if not defined SUMO_HOME (
    set "SUMO_HOME=C:\Program Files (x86)\SUMO"
)
if not exist "%SUMO_HOME%\bin\sumo.exe" (
    echo [WARNING] SUMO executable not found at %SUMO_HOME%\bin\sumo.exe
    echo [WARNING] Starting in simulated engine mode fallback.
) else (
    echo [OK] Eclipse SUMO verified at %SUMO_HOME%
)

REM 3. Check / Setup Python Virtual Environment
if not exist "backend\.venv\Scripts\python.exe" (
    echo [SMARTFLOW] Creating virtual environment...
    python -m venv backend\.venv
    call backend\.venv\Scripts\python -m pip install --upgrade pip
    call backend\.venv\Scripts\pip install -r backend\requirements.txt
)

REM 4. Check / Setup Frontend Dependencies
if not exist "frontend\node_modules" (
    echo [SMARTFLOW] Installing frontend node_modules...
    cd frontend
    call npm install
    cd ..
)

REM 5. Ensure safe backend .env exists
if not exist "backend\.env" (
    echo [SMARTFLOW] Generating local backend\.env...
    copy backend\.env.example backend\.env >nul
)

REM 6. Kill any previous stuck backend or SUMO processes
taskkill /F /IM sumo.exe >nul 2>&1
taskkill /F /IM sumo-gui.exe >nul 2>&1

echo [SMARTFLOW] Starting FastAPI backend on http://127.0.0.1:8000 ...
start "SMARTFLOW Backend" cmd /k "cd /d %~dp0backend && .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000"

REM 7. Wait until backend health check responds 200 OK
echo [SMARTFLOW] Waiting for backend to become healthy...
set /a attempts=0
:WAIT_LOOP
timeout /t 2 /nobreak >nul
set /a attempts+=1

powershell -Command "try { $r = Invoke-WebRequest -Uri 'http://127.0.0.1:8000/health' -UseBasicParsing -TimeoutSec 2; if ($r.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [OK] Backend is healthy and listening on http://127.0.0.1:8000
    goto START_FRONTEND
)

if %attempts% geq 15 (
    echo [ERROR] Backend failed to start within 30 seconds.
    echo Check the 'SMARTFLOW Backend' terminal window for Python tracebacks.
    pause
    exit /b 1
)
goto WAIT_LOOP

:START_FRONTEND
echo [SMARTFLOW] Starting Vite frontend on http://localhost:5173 ...
start "SMARTFLOW Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

timeout /t 3 /nobreak >nul

echo [SMARTFLOW] Opening application in default browser...
start http://localhost:5173

echo =========================================================================
echo SMARTFLOW ODISHA is running!
echo -------------------------------------------------------------------------
echo Frontend: http://localhost:5173
echo Backend:  http://127.0.0.1:8000/docs
echo Login:    admin@smartflow.local / ChangeMe123!
echo (Remember to change default password on first login)
echo =========================================================================
