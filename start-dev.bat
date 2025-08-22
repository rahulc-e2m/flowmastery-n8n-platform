@echo off
echo Starting FlowMastery Development Servers...
echo.

REM Start Backend Server
echo Starting Backend Server (Python FastAPI)...
start "Backend Server" cmd /k "cd backend && python app.py"

REM Wait a moment for backend to start
timeout /t 3 /nobreak

REM Start Frontend Server
echo Starting Frontend Server (React + Vite)...
start "Frontend Server" cmd /k "npm start"

echo.
echo Both servers are starting...
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173
echo.
echo Press any key to exit...
pause
