#!/bin/bash
# ------------------------------------------------------------
# setup.sh
#
# Ucel:
#   Kompletni jednorazova priprava vyvojoveho prostredi
#   pro MicroPython i CircuitPython ve VS Code na Linuxu a macOS:
#     1) Kontrola Pythonu 3 (chybi-li, nabidne instalaci spravcem
#        balicku: apt, dnf, zypper, pacman, brew - se sudo a otazkou)
#     2) Virtualni prostredi .venv v koreni projektu (na Ubuntu/Debianu
#        nabidne instalaci chybejiciho balicku python3.X-venv)
#     3) Instalace Python knihoven do .venv: mpremote (MicroPython,
#        obsahuje i pyserial) a matplotlib (graf: mpy plot / cpy plot)
#     4) Nastaveni panelu a Run on Save v settings.json
#        (zapisuje je .vscode/deska.py vscode - tlacitka jsou
#        definovana jen tam, stejne pro Windows i Linux/macOS).
#        Jde PRED instalaci rozsireni: panel si pri prvnim
#        spusteni precte uz prepsana tlacitka (python3), okno
#        neni potreba znovu nacitat.
#     5) Detekce VS Code CLI
#     6) Instalace rozsireni MicroPython & CircuitPython Panel (.vsix)
#     7) Hromadna instalace rozsireni z Marketplace
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
SCRIPT_VERSION="3.5"
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
# Instalace systemovych balicku (Python, python3-venv)
# ------------------------------------------------------------
# Python se na Linuxu instaluje do systemu spravcem balicku distribuce
# a potrebuje prava administratora (sudo + heslo). Skript proto
# nejdriv ukaze, co spusti, a zepta se. Bez terminalu (nelze se zeptat)
# nebo po odpovedi "n" jen vypise prikaz, ktery ma student spustit sam.

# Spravce balicku: apt (Ubuntu, Debian, Mint), dnf (Fedora), zypper
# (openSUSE), pacman (Arch, Manjaro), brew (macOS)
pkg_manager() {
    for pm in apt-get dnf zypper pacman brew; do
        if command -v "$pm" &>/dev/null; then
            echo "$pm"
            return
        fi
    done
}

# Prikaz instalace balicku pro dany spravce (bez sudo)
pkg_install_cmd() {
    local pm="$1"; shift
    case "$pm" in
        apt-get) echo "apt-get install -y $*" ;;
        dnf)     echo "dnf install -y $*" ;;
        zypper)  echo "zypper --non-interactive install $*" ;;
        pacman)  echo "pacman -S --noconfirm $*" ;;
        brew)    echo "brew install $*" ;;
    esac
}

# install_packages "popis" balicek... - zepta se a nainstaluje.
# Vrati 0, kdyz se instalace povedla.
install_packages() {
    local what="$1"; shift
    local pm
    pm=$(pkg_manager)
    if [ -z "$pm" ]; then
        echo "  Nenasel jsem spravce balicku (apt, dnf, zypper, pacman, brew)."
        echo "  Nainstalujte $what rucne a spustte ./setup.sh znovu."
        return 1
    fi
    local cmd sudo=""
    cmd=$(pkg_install_cmd "$pm" "$@")
    # brew a root sudo nepotrebuji
    if [ "$pm" != "brew" ] && [ "$(id -u)" != "0" ]; then
        if ! command -v sudo &>/dev/null; then
            echo "  Instalace potrebuje prava administratora a prikaz sudo neni k dispozici."
            echo "  Jako root spustte: $cmd"
            return 1
        fi
        sudo="sudo "
    fi
    echo "  Chybi $what. Lze ho nainstalovat prikazem:"
    echo "      $sudo$cmd"
    if [ ! -t 0 ]; then
        echo "  (Skript nebezi v terminalu, nemuze se zeptat - spustte prikaz sami.)"
        return 1
    fi
    local answer
    read -r -p "  Nainstalovat ted? [a/N] " answer
    case "$answer" in
        a|A|ano|Ano|y|Y|yes) ;;
        *)
            echo "  Neinstaluji. Spustte prikaz vyse sami a pak znovu ./setup.sh."
            return 1
            ;;
    esac
    [ -n "$sudo" ] && echo "  sudo se zepta na vase heslo (pri psani se nezobrazuje)."
    if [ "$pm" = "apt-get" ]; then
        # Seznam balicku muze byt stary (nebo v cerstvem systemu chybet)
        $sudo apt-get update || return 1
    fi
    $sudo $cmd
}

# ------------------------------------------------------------
# 1) Check Python
# ------------------------------------------------------------
echo "[1/8] Kontrola instalace Pythonu..."
find_python() {
    if command -v python3 &>/dev/null; then
        echo "python3"
    elif command -v python &>/dev/null && python -c 'import sys; sys.exit(sys.version_info[0] != 3)' 2>/dev/null; then
        echo "python"
    fi
}
PY=$(find_python)
if [ -z "$PY" ]; then
    echo "Python 3 nenalezen."
    case "$(pkg_manager)" in
        apt-get) PY_PKGS="python3 python3-venv" ;;
        pacman)  PY_PKGS="python" ;;
        brew)    PY_PKGS="python" ;;
        *)       PY_PKGS="python3" ;;
    esac
    # shellcheck disable=SC2086
    install_packages "Python 3" $PY_PKGS
    hash -r
    PY=$(find_python)
    if [ -z "$PY" ]; then
        echo "ERROR: Python 3 neni nainstalovany."
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
    make_venv() {
        echo "Vytvarim $VENV_DIR ..."
        if $PY -m venv "$VENV_DIR" && "$VENV_PY" -m pip --version &>/dev/null; then
            return 0
        fi
        rm -rf "$VENV_DIR"
        return 1
    }
    if ! make_venv; then
        # Ubuntu / Debian maji modul venv v samostatnem balicku podle
        # verze Pythonu: python3.12-venv, python3.11-venv, ...
        VENV_PKG=""
        if [ "$(pkg_manager)" = "apt-get" ]; then
            VENV_PKG="python$($PY -c 'import sys; print("%d.%d" % sys.version_info[:2])')-venv"
        fi
        if [ -n "$VENV_PKG" ] && install_packages "modul venv (balicek $VENV_PKG)" "$VENV_PKG" && make_venv; then
            :
        else
            echo "ERROR: Vytvoreni .venv selhalo."
            if [ -z "$VENV_PKG" ]; then
                echo "  Zkontrolujte, ze Python ($PY_VER) obsahuje modul venv a pip"
                echo "  (Ubuntu/Debian: balicek python3-venv), a spustte ./setup.sh znovu."
            fi
            exit 1
        fi
    fi
    echo ".venv vytvoreno."
fi
echo "--------------------------------------"

# ------------------------------------------------------------
# 3) Python knihovny do .venv
# ------------------------------------------------------------
echo "[3/8] Kontrola Python knihoven v .venv (mpremote, matplotlib, python-minifier)..."
# Povinne: mpremote (MicroPython) a python-minifier (zmenseni souboru pri
# nahravani - micro:bit ma jen asi 20 kB, viz docs/MicroBit.md)
if "$VENV_PY" -c "import mpremote, serial, python_minifier" &>/dev/null; then
    echo "mpremote a python-minifier OK"
else
    echo "mpremote / python-minifier nenalezen. Instaluji pres pip..."
    if ! "$VENV_PY" -m pip install --disable-pip-version-check mpremote python-minifier; then
        echo "ERROR: Instalace mpremote / python-minifier selhala."
        exit 1
    fi
    echo "mpremote a python-minifier uspesne nainstalovany."
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
# 4) Nastaveni settings.json pro Linux / macOS
# ------------------------------------------------------------
echo "[4/8] Nastaveni panelu a Run on Save (settings.json)..."

# Tlacitka panelu i Run on Save jsou definovana v deska.py (PANEL_BUTTONS),
# aby byla stejna pro Windows i Linux/macOS.
if ! $PY "$DESKA_PY" vscode; then
    echo "  -> Upozorneni: settings.json se nepodarilo nastavit."
fi
echo "--------------------------------------"

# ------------------------------------------------------------
# 5) Detekce VS Code CLI
# ------------------------------------------------------------
echo "[5/8] Detekce rozhrani VS Code CLI..."
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
# 6) Instalace MicroPython & CircuitPython Panelu (.vsix)
# ------------------------------------------------------------
echo "[6/8] Instalace rozsireni MicroPython & CircuitPython Panel..."
# Prikaz "code" bezi na Node.js a pri instalaci rozsireni vypisuje varovani
# "DeprecationWarning: url.parse()". Neni to chyba, jen by studenta zbytecne
# vystrasilo - promenna NODE_NO_WARNINGS ho skryje.
export NODE_NO_WARNINGS=1
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
# 7) Hromadne instalace rozsireni z Marketplace
# ------------------------------------------------------------
echo "[7/8] Instalace spolecnych rozsireni z Marketplace..."
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
# 8) Detekce pripojeneho hardware
# ------------------------------------------------------------
echo "[8/8] Kontrola pripojenych desek..."

# Vypise desky s CircuitPythonem (disk CIRCUITPY) i MicroPythonem (port).
# Kdyz neni pripojena zadna deska, nevadi to - prostredi je pripraveno.
$PY "$DESKA_PY" devices

echo "============================================================"
if [ -n "$CODE_CMD" ]; then
    echo "  Instalace je KOMPLETNI! Prostredi je pripraveno."
    echo "  Muzete pracovat s MicroPythonem i CircuitPythonem."
else
    echo "  Instalace NENI kompletni: chybi rozsireni VS Code."
    echo "  Python, knihovny a nastaveni jsou pripravene. Ve VS Code stisknete"
    echo "  F1 -> 'Shell Command: Install code command in PATH' a spustte"
    echo "  ./setup.sh znovu."
fi
echo "============================================================"
