@echo off
setlocal
REM Keep this file ASCII so Windows cmd.exe can read it on any code page.
cd /d "%~dp0"
if "%~1"=="--service" goto service

echo Checking development environment...
set "DEV_PYTHON=python"
if exist "%~dp0venv\Scripts\python.exe" set "DEV_PYTHON=%~dp0venv\Scripts\python.exe"
if exist "%~dp0.venv\Scripts\python.exe" set "DEV_PYTHON=%~dp0.venv\Scripts\python.exe"
if exist "%~dp0adminAPI\venv\Scripts\python.exe" set "DEV_PYTHON=%~dp0adminAPI\venv\Scripts\python.exe"
if exist "%~dp0adminAPI\.venv\Scripts\python.exe" set "DEV_PYTHON=%~dp0adminAPI\.venv\Scripts\python.exe"

"%DEV_PYTHON%" -c "import django, daphne, channels" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python or backend dependencies missing. See DEV-START.md.
    goto failed
)
node -e "const [m,n]=process.versions.node.split('.').map(Number); process.exit((m===22 && n>=14) || m>=24 ? 0 : 1)" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js 22.14+ in the 22.x series, or 24+ is required.
    goto failed
)
for %%S in (admin customer seller) do (
    if not exist "%%S\node_modules\vite\bin\vite.js" (
        echo ERROR: Dependencies missing in %%S. Run npm ci in that directory.
        goto failed
    )
)
REM Refuse occupied ports; never kill another project or silently change ports.
powershell.exe -NoProfile -Command "$ports = @(8000,5173,5174,5175); $busy = @([System.Net.NetworkInformation.IPGlobalProperties]::GetIPGlobalProperties().GetActiveTcpListeners() | Where-Object { $_.Port -in $ports } | Select-Object -ExpandProperty Port -Unique); if ($busy.Count) { Write-Host ('ERROR: Ports already in use: ' + ($busy -join ', ')); exit 1 }"
if errorlevel 1 goto failed
if "%~1"=="--check" (
    echo Checks passed. No services started.
    exit /b 0
)

REM Variables are inherited by the four service windows, not saved to .env.
set "VITE_DEV_BACKEND=http://127.0.0.1:8000"
set "VITE_API_BASE_URL=/api"
set "PYTHONUNBUFFERED=1"
start "Ecommerce - Django :8000" "%ComSpec%" /d /k ""%~f0" --service django"
start "Ecommerce - Admin :5173" "%ComSpec%" /d /k ""%~f0" --service admin"
start "Ecommerce - Customer :5174" "%ComSpec%" /d /k ""%~f0" --service customer"
start "Ecommerce - Seller :5175" "%ComSpec%" /d /k ""%~f0" --service seller"
echo.
echo Service windows opened. Check each window for startup errors.
echo Admin:    http://localhost:5173
echo Customer: http://localhost:5174
echo Seller:   http://localhost:5175
echo Stop all: double-click stop-dev.bat
echo Stop one: press Ctrl+C in its window.
pause
exit /b 0

:service
if "%~2"=="django" (
    title Ecommerce - Django :8000
    cd /d "%~dp0adminAPI"
    "%DEV_PYTHON%" -m daphne -b 127.0.0.1 -p 8000 config.asgi:application
    goto ended
)
if "%~2"=="admin" set "DEV_PORT=5173"
if "%~2"=="customer" set "DEV_PORT=5174"
if "%~2"=="seller" set "DEV_PORT=5175"
if not defined DEV_PORT exit /b 1
title Ecommerce - %~2 :%DEV_PORT%
cd /d "%~dp0%~2"
REM package.json dev scripts currently run only vite. Direct invocation keeps
REM the service window title stable and avoids an extra npm command shell.
node node_modules\vite\bin\vite.js --host localhost --port %DEV_PORT% --strictPort
:ended
echo.
echo Service exited. Review the output above. Close this window when finished.
exit /b

:failed
echo Nothing was started. See DEV-START.md for setup and troubleshooting.
if not "%~1"=="--check" pause
exit /b 1
