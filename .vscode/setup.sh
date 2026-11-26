#!/bin/bash
# ------------------------------------------------------------
# setup.sh
#
# Ucel:
#   Kompletni jednorazova priprava vyvojoveho prostredi
#   pro MicroPython i CircuitPython ve VS Code na Linuxu a macOS:
#     1) Kontrola Pythonu 3
#     2) Virtualni prostredi .venv v koreni projektu
#     3) Instalace Python knihoven do .venv: mpremote (MicroPython,
#        obsahuje i pyserial) a matplotlib (graf: mpy plot / cpy plot)
#     4) Detekce VS Code CLI
#     5) Instalace rozsireni MicroPython & CircuitPython Panel (.vsix)
#     6) Hromadna instalace rozsireni z Marketplace
#     7) Nastaveni panelu a Run on Save v settings.json
#        (zapisuje je .vscode/deska.py vscode - tlacitka jsou
#        definovana jen tam, stejne pro Windows i Linux/macOS)
#     8) Kontrola pripojenych desek (.vscode/deska.py devices)
#
# Knihovny jdou do .venv (jen pro tento projekt). Novejsi Linuxy
# (Ubuntu 23.04+, Debian 12+) instalaci pres pip mimo virtualni
# prostredi odmitaji (chyba externally-managed-environment, PEP 668).
# deska.py si .venv najde sam, prikazy v settings.json proto
# zustavaji "python3 .vscode/deska.py ...".
#
# Vsechny ostatni nastroje (mpy, cpy) jsou v jedinem souboru
# .vscode/deska.py. Tento skript zustava v bashi, protoze musi
# umet zkontrolovat i samotny Python.
# ------------------------------------------------------------
SCRIPT_NAME="setup.sh"
SCRIPT_VERSION="3.2"
SCRIPT_DATE="2026-11-26"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DESKA_PY="$SCRIPT_DIR/deska.py"
VENV_DIR="$PROJECT_ROOT/.venv"
VENV_PY="$VENV_DIR/bin/python"

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
        echo "  Na Ubuntu/Debian nainstalujte: sudo apt install python3 python3-venv"
        echo "  Na macOS nainstalujte: brew install python"
        exit 1
    fi
fi
PY_VER=$($PY --version 2>&1)
echo "Python OK ($PY_VER)"
echo "--------------------------------------"

# ------------------------------------------------------------
# 2) Virtualni prostredi .venv
# ------------------------------------------------------------
echo "[2/8] Virtualni prostredi .venv (knihovny jen pro tento projekt)..."
if [ -x "$VENV_PY" ] && "$VENV_PY" -m pip --version &>/dev/null; then
    echo ".venv OK"
else
    if [ -e "$VENV_DIR" ]; then
        # Napr. Python, ze ktereho .venv vzniklo, byl aktualizovan/odinstalovan,
        # nebo predchozi pokus skoncil chybou (chybejici python3-venv).
        echo "Stavajici .venv nefunguje, vytvarim ho znovu..."
        rm -rf "$VENV_DIR"
    fi
    echo "Vytvarim $VENV_DIR ..."
    if ! $PY -m venv "$VENV_DIR" || ! "$VENV_PY" -m pip --version &>/dev/null; then
        rm -rf "$VENV_DIR"
        echo "ERROR: Vytvoreni .venv selhalo."
        echo "  Na Ubuntu/Debian nainstalujte: sudo apt install python3-venv"
        echo "  (pripadne python3.X-venv podle verze: $($PY --version 2>&1))"
        echo "  a spustte ./setup.sh znovu."
        exit 1
    fi
    echo ".venv vytvoreno."
fi
echo "--------------------------------------"

# ------------------------------------------------------------
# 3) Python knihovny do .venv
# ------------------------------------------------------------
echo "[3/8] Kontrola Python knihoven v .venv (mpremote, matplotlib)..."
if "$VENV_PY" -c "import mpremote, serial" &>/dev/null; then
    echo "mpremote OK"
else
    echo "mpremote nenalezen. Instaluji pres pip..."
    if ! "$VENV_PY" -m pip install --disable-pip-version-check mpremote; then
        echo "ERROR: Instalace mpremote selhala."
        exit 1
    fi
    echo "mpremote uspesne nainstalovan."
fi

# matplotlib je potreba jen pro graf (mpy plot / cpy plot)
if "$VENV_PY" -c "import matplotlib" &>/dev/null; then
    echo "matplotlib OK"
else
    echo "matplotlib (graf) nenalezen. Instaluji pres pip..."
    if "$VENV_PY" -m pip install --disable-pip-version-check matplotlib; then
        echo "matplotlib uspesne nainstalovan."
    else
        echo "Instalace matplotlib selhala (graf nebude fungovat, ostatni ano)."
    fi
fi
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
