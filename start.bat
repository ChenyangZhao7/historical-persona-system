@echo off
cd /d "%~dp0"
title Historical Persona System

echo ================================================
echo   Historical Persona System
echo   API : http://127.0.0.1:8000
echo   Web : http://localhost:5173
echo ================================================
echo.

if not exist "venv\Scripts\python.exe" (
    echo [ERROR] venv not found: venv\Scripts\python.exe
    echo Run these first:
    echo   uv venv --python 3.12 venv
    echo   uv pip install --python .\venv\Scripts\python.exe -r backend\requirements.txt
    echo.
    pause
    exit /b 1
)

if not exist "node_modules" (
    echo [ERROR] node_modules not found
    echo Run these first:
    echo   npm install
    echo   npm --prefix frontend install
    echo.
    pause
    exit /b 1
)

if not exist ".env" (
    echo [WARN] .env not found - AI features will fail.
    echo Copy .env.example to .env and add DEEPSEEK_API_KEY.
    echo.
    pause
)

echo Starting backend and frontend...
echo First start takes 5-10 seconds. The browser opens by itself.
echo To stop: press Ctrl+C in this window, or just close it.
echo.

start "" cmd /c "timeout /t 8 >nul & start http://localhost:5173"

call npm start

echo.
echo Server stopped.
pause
