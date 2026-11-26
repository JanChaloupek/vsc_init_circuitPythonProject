#!/bin/bash
# mpy - spoustec nastroje pro MicroPython (Linux / macOS).
# Cela logika je v .vscode/deska.py, prikazy vypise: ./mpy.sh help
PY="python3"
if ! command -v python3 &>/dev/null; then
    PY="python"
fi
exec "$PY" "$(dirname "$0")/.vscode/deska.py" mpy "$@"
