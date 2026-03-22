@echo off
REM Start the Agent Graph Dashboard - Windows Version

echo ==============================================
echo   Agent Graph Dashboard - Startup Script
echo ==============================================

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install Python dependencies
echo Installing Python dependencies...
pip install -e . -q

REM Check if Node modules exist
if not exist "frontend\node_modules" (
    echo Installing frontend dependencies...
    cd frontend
    call npm install
    cd ..
)

REM Set environment variable reminder
echo.
echo ==============================================
echo   IMPORTANT: Set your API key before running
echo ==============================================
echo   set OPENROUTER_API_KEY=your_key_here
echo.

REM Start the server in background
echo Starting FastAPI server on http://localhost:8000...
start "FastAPI Server" cmd /k "python -m uvicorn src.server:app_api --host 0.0.0.0 --port 8000"

REM Wait for server to start
timeout /t 5 /nobreak >nul

REM Start the frontend
echo Starting frontend dev server...
cd frontend
start "Frontend Dev Server" cmd /k "npm run dev"
cd ..

echo.
echo ==============================================
echo   Dashboard is starting...
echo   - API: http://localhost:8000
echo   - Frontend: http://localhost:5173
echo ==============================================
echo.
echo Press any key to exit this window...
pause >nul
