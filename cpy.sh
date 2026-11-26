#!/bin/bash
# cpy - spoustec nastroje pro CircuitPython (Linux / macOS).
# Cela logika je v .vscode/deska.py, prikazy vypise: ./cpy.sh help
PY="python3"
if ! command -v python3 &>/dev/null; then
    PY="python"
fi
exec "$PY" "$(dirname "$0")/.vscode/deska.py" cpy "$@"
