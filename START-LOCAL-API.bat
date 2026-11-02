@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo The project Python environment is missing at .venv\Scripts\python.exe.
  echo Open PowerShell in this folder and create the environment before starting the API.
  pause
  exit /b 1
)

echo Starting the Candidex API on http://localhost:8000
echo Keep this window open while using the website. Press Ctrl+C only when you want to stop the API.
".venv\Scripts\python.exe" -m uvicorn app.main:app --app-dir apps/api --host 127.0.0.1 --port 8000

echo The API process has stopped.
pause
