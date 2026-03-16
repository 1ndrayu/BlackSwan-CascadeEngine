@echo off
setlocal
title CASCADE RISK ENGINE: Fracture Telemetry

echo [1/3] Checking environment...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in your PATH.
    echo Please install Python from https://www.python.org/
    pause
    exit /b 1
)

echo [2/3] Installing/Verifying dependencies (numpy, scipy, matplotlib)...
python -m pip install numpy scipy matplotlib >nul 2>&1

echo [3/3] Launching CASCADE RISK ENGINE Dashboard...
echo Dashboard will be available at http://localhost:8081

:: Start the server in a new window so it stays running
start "CASCADE RISK ENGINE Server" cmd /c "cd /d %~dp0 && python server.py"

:: Give it a second to spin up
timeout /t 2 /nobreak >nul

:: Open the browser
start http://localhost:8081

echo.
echo [SUCCESS] CASCADE RISK ENGINE is live! 
echo Keep the server terminal window open while using the dashboard.
echo.
pause
