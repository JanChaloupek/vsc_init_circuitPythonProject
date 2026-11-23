@echo off
setlocal
echo ============================================================
echo   Spoustim instalaci prostredi pro MicroPython...
echo ============================================================
echo.

powershell.exe -ExecutionPolicy Bypass -NoProfile -File "%~dp0setup-MicroPython.ps1"

echo.
pause
