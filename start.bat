@echo off
REM Start both backend and frontend

echo Starting backend server...
start "Backend" python main.py

timeout /t 3 /nobreak >nul

echo Starting frontend dev server...
cd frontend
start "Frontend" npm run dev

echo.
echo ========================================
echo Document Query System
echo ========================================
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo ========================================
echo.
echo Press Ctrl+C to stop both servers, or close these windows
pause
