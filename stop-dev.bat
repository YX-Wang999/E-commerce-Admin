@echo off
setlocal
REM Identify only cmd windows launched by this project's start-dev.bat.
REM Kill their process trees, never every node.exe/python.exe on the machine.
set "DEV_START_SCRIPT=%~dp0start-dev.bat"
powershell.exe -NoProfile -Command "$ErrorActionPreference = 'Stop'; try { $windows = @(Get-CimInstance Win32_Process -Filter 'Name = ''cmd.exe''' | Where-Object { $_.CommandLine -and $_.CommandLine.IndexOf($env:DEV_START_SCRIPT, [StringComparison]::OrdinalIgnoreCase) -ge 0 -and $_.CommandLine -match '--service (django|admin|customer|seller)(?:\s|\x22|$)' }); if (-not $windows.Count) { Write-Host 'No development service windows found.' }; $failed = $false; foreach ($window in $windows) { taskkill.exe /PID $window.ProcessId /T /F; if ($LASTEXITCODE -ne 0) { $failed = $true } }; if ($failed) { exit 1 } } catch { Write-Host $_; exit 1 }"
if errorlevel 1 (
    echo Could not stop every service. Use Ctrl+C in the remaining windows.
    pause
    exit /b 1
)
echo Development services stopped.
pause
