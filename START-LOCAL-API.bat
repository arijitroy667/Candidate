@echo off
setlocal
cd /d "%~dp0"

rem Always use the machine-local resume store for the local demo, even if the
rem parent PowerShell session has APP_ENV=production set.
set "APP_ENV=local"

if not exist ".venv\Scripts\python.exe" (
  echo The project Python environment is missing at .venv\Scripts\python.exe.
  echo Open PowerShell in this folder and create the environment before starting the API.
  pause
  exit /b 1
)

echo Starting the Candidex API on http://localhost:8000
echo Resume storage: local project folder (apps\api\local-storage)
echo Keep this window open while using the website. Press Ctrl+C only when you want to stop the API.
".venv\Scripts\python.exe" -m uvicorn app.main:app --app-dir apps/api --host 127.0.0.1 --port 8000

echo The API process has stopped.
pause
