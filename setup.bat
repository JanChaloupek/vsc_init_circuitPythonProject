@echo off
setlocal
powershell.exe -ExecutionPolicy Bypass -NoProfile -File "%~dp0.vscode\setup.ps1"
echo.
pause
