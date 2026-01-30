@echo off
REM Social-Hunt Universal Startup Wrapper (Windows)
REM This script calls the Python startup script

cd /d "%~dp0"

REM Try python3 first, then python
python3 start.py
if %errorlevel% neq 0 (
    python start.py
)

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3 or run: docker compose up -d
    echo.
    pause
    exit /b 1
)

pause
