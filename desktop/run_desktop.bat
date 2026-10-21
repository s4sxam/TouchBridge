@echo off
setlocal
echo ========================================================
echo        TouchBridge Universal - Launching Desktop App
echo ========================================================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.11+ from https://www.python.org/
    pause
    exit /b 1
)

REM Install required packages if missing
echo [INFO] Checking Python dependencies...
python -m pip install -q -r requirements.txt

REM Launch the application
echo [INFO] Starting TouchBridge Desktop...
set PYTHONPATH=%~dp0
python -m touchbridge.main %*

if errorlevel 1 (
    echo [ERROR] Application exited with an error.
    pause
)
