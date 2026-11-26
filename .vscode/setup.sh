#!/bin/bash
# ------------------------------------------------------------
# setup.sh
#
# Ucel:
#   Kompletni jednorazova priprava vyvojoveho prostredi
#   pro MicroPython i CircuitPython ve VS Code na Linuxu a macOS:
#     1) Kontrola Pythonu 3
#     2) Kontrola balickovaciho nastroje pip
#     3) Instalace Python knihoven: mpremote (MicroPython, obsahuje
#        i pyserial) a matplotlib (graf hodnot: mpy plot / cpy plot)
#     4) Detekce VS Code CLI
#     5) Instalace rozsireni MicroPython & CircuitPython Panel (.vsix)
#     6) Hromadna instalace rozsireni z Marketplace
#     7) Nastaveni panelu a Run on Save v settings.json
#        (zapisuje je .vscode/deska.py vscode - tlacitka jsou
#        definovana jen tam, stejne pro Windows i Linux/macOS)
#     8) Kontrola pripojenych desek (.vscode/deska.py devices)
#
# Vsechny ostatni nastroje (mpy, cpy) jsou v jedinem souboru
# .vscode/deska.py. Tento skript zustava v bashi, protoze musi
# umet zkontrolovat i samotny Python.
# ------------------------------------------------------------
SCRIPT_NAME="setup.sh"
SCRIPT_VERSION="3.0"
SCRIPT_DATE="2026-11-26"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DESKA_PY="$SCRIPT_DIR/deska.py"

echo "============================================================"
echo "  $SCRIPT_NAME - verze: $SCRIPT_VERSION ($SCRIPT_DATE)"
echo "  Kompletni priprava prostredi: MicroPython & CircuitPython"
echo "  Platforma: Linux / macOS"
echo "============================================================"
echo ""

# Nastaveni prav spusteni pro skripty (setup, spoustece mpy.sh / cpy.sh)
chmod +x "$SCRIPT_DIR"/*.sh "$PROJECT_ROOT"/*.sh 2>/dev/null

# ------------------------------------------------------------
# 1) Check Python
# ------------------------------------------------------------
echo "[1/8] Kontrola instalace Pythonu..."
PY="python3"
if ! command -v python3 &>/dev/null; then
    if command -v python &>/dev/null; then
        PY="python"
    else
        echo "ERROR: Python 3 nenalezen."
        echo "  Na Ubuntu/Debian nainstalujte: sudo apt install python3 python3-pip"
        echo "  Na macOS nainstalujte: brew install python"
        exit 1
    fi
fi
PY_VER=$($PY --version 2>&1)
echo "Python OK ($PY_VER)"
echo "--------------------------------------"

# ------------------------------------------------------------
# 2) Check pip
# ------------------------------------------------------------
echo "[2/8] Kontrola balickovaciho nastroje pip..."
$PY -m pip --version &>/dev/null
if [ $? -ne 0 ]; then
    echo "pip nenalezen. Zkousim ensurepip..."
    $PY -m ensurepip --default-pip
    if [ $? -ne 0 ]; then
        echo "ERROR: Instalace pip selhala."
        echo "  Na Ubuntu/Debian: sudo apt install python3-pip"
        exit 1
    fi
fi
echo "pip OK"
echo "--------------------------------------"

# ------------------------------------------------------------
# 3) Check mpremote
# ------------------------------------------------------------
echo "[3/8] Kontrola Python knihoven (mpremote, matplotlib)..."
$PY -m mpremote --help &>/dev/null
if [ $? -ne 0 ]; then
    echo "mpremote nenalezen. Instaluji pres pip..."
    $PY -m pip install mpremote
    if [ $? -ne 0 ]; then
        echo "ERROR: Instalace mpremote selhala."
        exit 1
    fi
fi
echo "mpremote OK"

# matplotlib je potreba jen pro graf (mpy plot / cpy plot)
if ! $PY -c "import matplotlib" &>/dev/null; then
    echo "matplotlib (graf) nenalezen. Instaluji pres pip..."
    if ! $PY -m pip install matplotlib; then
        echo "Instalace matplotlib selhala (graf nebude fungovat, ostatni ano)."
    fi
fi
echo "matplotlib OK"
echo "--------------------------------------"

# ------------------------------------------------------------
# 4) Detekce VS Code CLI
# ------------------------------------------------------------
echo "[4/8] Detekce rozhrani VS Code CLI..."
CODE_CMD=""
if command -v code &>/dev/null; then
    CODE_CMD="code"
elif [ -f "/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code" ]; then
    CODE_CMD="/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code"
elif command -v code-insiders &>/dev/null; then
    CODE_CMD="code-insiders"
fi

if [ -z "$CODE_CMD" ]; then
    echo "UPOZORNENI: VS Code CLI ('code') nenalezen v PATH."
    echo "  V editoru VS Code stisknete F1 -> 'Shell Command: Install code command in PATH'."
    echo "  Preskakuji automatickou instalaci rozsireni."
else
    echo "VS Code CLI nalezen: $CODE_CMD"
fi
echo "--------------------------------------"

# ------------------------------------------------------------
# 5) Instalace MicroPython & CircuitPython Panelu (.vsix)
# ------------------------------------------------------------
echo "[5/8] Instalace rozsireni MicroPython & CircuitPython Panel..."
VSIX="$SCRIPT_DIR/dist/micropython-panel.vsix"
if [ -n "$CODE_CMD" ]; then
    if [ -f "$VSIX" ]; then
        "$CODE_CMD" --install-extension "$VSIX" --force
        if [ $? -eq 0 ]; then
            echo "MicroPython & CircuitPython Panel uspesne nainstalovan/aktualizovan."
        else
            echo "Instalace panelu selhala."
        fi
    else
        echo "Upozorneni: Balicek $VSIX nebyl nalezen."
    fi
fi
echo "--------------------------------------"

# ------------------------------------------------------------
# 6) Hromadne instalace rozsireni z Marketplace
# ------------------------------------------------------------
echo "[6/8] Instalace spolecnych rozsireni z Marketplace..."
EXTENSIONS=(
    "ms-python.python"
    "ms-python.vscode-pylance"
    "wmerkens.vscode-circuitpython-v2-cursor-ai"
    "emeraldwalk.runonsave"
    "streetsidesoftware.code-spell-checker"
    "streetsidesoftware.code-spell-checker-czech"
    "oderwat.indent-rainbow"
    "ms-vscode.powershell"
    "jebbs.plantuml"
    "IBM.output-colorizer"
    "eugenejeon.codesnap-plus-fix"
)

if [ -n "$CODE_CMD" ]; then
    for ext in "${EXTENSIONS[@]}"; do
        echo "  -> Instaluji $ext ... "
        "$CODE_CMD" --install-extension "$ext" --force &>/dev/null
        if [ $? -eq 0 ]; then
            echo "     [OK]"
        else
            echo "     [CHYBA]"
        fi
    done
fi
echo "--------------------------------------"

# ------------------------------------------------------------
# 7) Nastaveni settings.json pro Linux / macOS
# ------------------------------------------------------------
echo "[7/8] Nastaveni panelu a Run on Save (settings.json)..."

# Tlacitka panelu i Run on Save jsou definovana v deska.py (PANEL_BUTTONS),
# aby byla stejna pro Windows i Linux/macOS.
if ! $PY "$DESKA_PY" vscode; then
    echo "  -> Upozorneni: settings.json se nepodarilo nastavit."
fi
echo "--------------------------------------"

# ------------------------------------------------------------
# 8) Detekce pripojeneho hardware
# ------------------------------------------------------------
echo "[8/8] Kontrola pripojenych desek..."

# Vypise desky s CircuitPythonem (disk CIRCUITPY) i MicroPythonem (port).
# Kdyz neni pripojena zadna deska, nevadi to - prostredi je pripraveno.
$PY "$DESKA_PY" devices

echo "============================================================"
echo "  Instalace je KOMPLETNI! Prostredi je pripraveno."
echo "  Muzete pracovat s MicroPythonem i CircuitPythonem."
echo "============================================================"
