@echo off
echo Starting Adaptive Trust-Aware Persuasion System...

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH.
    pause
    exit /b
)

:: Install dependencies (optional, can be commented out after first run)
echo Checking dependencies...
pip install -r requirements_web.txt

:: Start Backend
echo Starting Backend Server...
python start_backend.py

pause
