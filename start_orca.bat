@echo off
echo ===================================================
echo   ORCA DASHBOARD STARTUP
echo ===================================================
echo.

:: 1. Check Python Environment
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found! Please install Python 3.9+ and add to PATH.
    pause
    exit /b 1
)

:: 2. Launch Python Controller
python launcher.py

echo.
echo Launcher has exited.
pause
