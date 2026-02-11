@echo off
setlocal enabledelayedexpansion

echo ===================================================
echo   ORCA DASHBOARD SHUTDOWN
echo ===================================================
echo.

:: List of ports used by ORCA and its providers
:: 5005: Orpheus TTS
:: 7010: ORCA Runtime
:: 8001: ORCA Backend
:: 5173: ORCA Frontend
:: 1234: LM Studio (if started by ORCA)
:: 11434: Ollama (if started by ORCA)

set PORTS=5005 7010 8001 5173 1234 11434

for %%P in (%PORTS%) do (
    echo [INFO] Searching for process on port %%P...
    for /f "tokens=5" %%A in ('netstat -aon ^| findstr :%%P ^| findstr LISTENING') do (
        echo [KILL] Found PID %%A on port %%P. Terminating...
        taskkill /F /PID %%A >nul 2>&1
    )
)

:: Attempt to close any remaining CMD windows launched by the launcher
echo [INFO] Closing remaining ORCA terminal windows...
taskkill /F /FI "WINDOWTITLE eq ORCA*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq Orpheus*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq LM Studio*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq Ollama*" >nul 2>&1

echo.
echo ===================================================
echo   [SUCCESS] ORCA services have been shut down.
echo ===================================================
echo.
pause
