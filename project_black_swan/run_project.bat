@echo off
setlocal enabledelayedexpansion
title CASCADE RISK ENGINE: Fracture Telemetry

cd /d "%~dp0"

echo ==================================================
echo  CASCADE RISK ENGINE - Setup
echo ==================================================

python --version >nul 2>&1
if !errorlevel! neq 0 (
    echo [ERROR] Python not found.
    pause
    exit /b 1
)

if not exist .venv (
    echo [1/3] Creating venv...
    python -m venv .venv
) else (
    echo [1/3] venv exists.
)

echo [2/3] Installing dependencies...
call .venv\Scripts\activate
python -m pip install -r requirements.txt

echo [3/3] Launching...
start "CASCADE Server" cmd /c "call .venv\Scripts\activate && python server.py"
timeout /t 3 /nobreak >nul
start http://localhost:8081

echo [SUCCESS] Running!
pause
