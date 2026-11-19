@echo off
echo ====================================================
echo Starting ScriptForge AI (Backend + Frontend)
echo ====================================================

REM Start Backend
start "ScriptForge AI Backend (Port 8000)" cmd /k "cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

REM Start Frontend
start "ScriptForge AI Frontend (Port 3000)" cmd /k "cd frontend && pnpm run dev"

echo.
echo ScriptForge AI is starting!
echo Backend API:  http://localhost:8000 (Docs: http://localhost:8000/docs)
echo Frontend UI:  http://localhost:3000
echo.
pause
