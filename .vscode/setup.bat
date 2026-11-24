@echo off
setlocal
echo ============================================================
echo   Kompletni priprava vyvojoveho prostredi
echo   (MicroPython i CircuitPython pro robotiku)
echo ============================================================
echo.

powershell.exe -ExecutionPolicy Bypass -NoProfile -File "%~dp0setup.ps1"

echo.
pause
