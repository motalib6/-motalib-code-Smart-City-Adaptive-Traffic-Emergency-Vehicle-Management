@echo off
REM SMARTFLOW ODISHA — one-click start on Windows.
REM Run this from the repo root. Needs Python 3.11+ and Node.js installed.
REM Backend: http://127.0.0.1:8000/docs   Frontend: http://localhost:5173
setlocal
cd /d %~dp0
if not exist backend\.venv (
  echo Creating Python venv...
  py -m venv backend\.venv
  backend\.venv\Scripts\python -m pip install --upgrade pip
  backend\.venv\Scripts\pip install -r backend\requirements.txt
)
if not exist frontend\node_modules (
  echo Installing frontend deps...
  cd frontend && call npm install && cd ..
)
start "SMARTFLOW backend" cmd /k "cd backend && ..\.venv\Scripts\uvicorn app.main:app --reload --port 8000"
start "SMARTFLOW frontend" cmd /k "cd frontend && npm run dev"
echo Backend: http://127.0.0.1:8000/docs
echo Frontend: http://localhost:5173
echo Login: admin@smartflow.local / ChangeMe123!  (change after first login)
pause
