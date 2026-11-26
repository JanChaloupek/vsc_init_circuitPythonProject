@echo off
rem cpy - spoustec nastroje pro CircuitPython (Windows).
rem Cela logika je v .vscode\deska.py, prikazy vypise: cpy help
python "%~dp0.vscode\deska.py" cpy %*
