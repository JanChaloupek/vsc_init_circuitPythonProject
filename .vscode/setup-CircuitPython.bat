@echo off
setlocal
echo ============================================================
echo   Spoustim instalaci prostredi pro CircuitPython...
echo ============================================================
echo.

powershell.exe -ExecutionPolicy Bypass -NoProfile -File "%~dp0setup-CircuitPython.ps1"

echo.
pause
