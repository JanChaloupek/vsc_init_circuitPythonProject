#!/usr/bin/env python3
# ============================================================
# deska.py - nastroj pro praci s deskami s MicroPythonem a CircuitPythonem
#
# Verze: 2.1 (2026-11-26)
#
# K CEMU TO JE
#   Jeden soubor, ktery umi nahrat program do desky, spustit ho,
#   otevrit konzoli (REPL), vypsat a smazat soubory, zobrazit graf
#   hodnot a zjistit, jake desky jsou pripojene. Funguje stejne ve
#   Windows, v Linuxu i v macOS (je to Python, ne PowerShell/bash).
#
# JAK SE TO SPOUSTI
#   Obvykle pres kratke spoustece v koreni projektu:
#       Windows (PowerShell):   .\mpy upload        .\cpy upload
#       Windows (cmd):          mpy upload          cpy upload
#       Linux / macOS:          ./mpy.sh upload     ./cpy.sh upload
#   Nebo primo (to dela i panel ve VS Code):
#       python .vscode/deska.py mpy upload
#       python .vscode/deska.py cpy upload
#   Spolecne prikazy:
#       python .vscode/deska.py devices   ... jake desky jsou pripojene
#       python .vscode/deska.py vscode    ... nastavi panel a Run on Save
#                                             v .vscode/settings.json
#
# DVE SADY PRIKAZU - PROC SE LISI
#   mpy = MicroPython (BBC micro:bit, Raspberry Pi Pico, Pico:ed v2)
#       Deska nema USB disk. Vsechno (kopirovani souboru, spusteni,
#       vypis) jde pres seriovou linku nastrojem mpremote. Jinak to
#       u MicroPythonu nejde.
#   cpy = CircuitPython (Pico:ed v1 a v2)
#       Deska se v pocitaci ukaze jako USB disk CIRCUITPY. Soubory se
#       proto kopiruji PRIMO NA DISK (stejne jako pri Ctrl+S v editoru)
#       a CircuitPython po zapisu sam znovu spusti code.py (autoreload).
#       Seriova linka se pouziva jen tam, kde to jinak nejde
#       (zastaveni programu, REPL, spusteni z RAM, restart, ...).
#
# OBSAH SOUBORU (hledej nadpisy "ODDIL")
#   ODDIL 1  Nastaveni a tabulky desek
#   ODDIL 2  Vypis na obrazovku (barvy, hlasky)
#   ODDIL 3  Hledani desek (USB disky, seriove porty)
#   ODDIL 4  Seriova konzole desky (REPL a raw REPL)
#   ODDIL 5  Soubory projektu (.ignoreCopy) a stromovy vypis
#   ODDIL 6  Spolecne prikazy (devices, vscode, graf)
#   ODDIL 7  CircuitPython - prikazy cpy
#   ODDIL 8  MicroPython - prikazy mpy
#   ODDIL 9  Napoveda, cteni parametru a hlavni funkce
#
# CO POTREBUJE
#   - Python 3.8 nebo novejsi
#   - mpremote   - komunikace s MicroPythonem, obsahuje i pyserial
#   - matplotlib - jen pro graf (plot)
#   - circup     - jen pro cpy lib (setup ho neinstaluje)
#   Knihovny instaluje setup.bat / setup.sh do virtualniho prostredi
#   .venv v koreni projektu (jen pro tento projekt, systemovy Python
#   zustane cisty). Kdyz .venv existuje, deska.py se v nem sam spusti
#   znovu - prikazy proto staci psat s obycejnym "python" / "python3".
# ============================================================
import contextlib
import fnmatch
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
from collections import deque
from pathlib import Path

SCRIPT_NAME = "deska.py"
SCRIPT_VERSION = "2.1"
SCRIPT_DATE = "2026-11-26"


# ============================================================
# ODDIL 1  Nastaveni a tabulky desek
# ============================================================
HERE = Path(__file__).resolve().parent          # slozka .vscode
PROJECT = HERE.parent                            # koren projektu
IGNORE_FILE = HERE / ".ignoreCopy"               # co se NEnahrava na CircuitPython
UPLOAD_CONFIG = HERE / "upload_config.txt"       # co se nahrava na MicroPython
SETTINGS_FILE = HERE / "settings.json"           # nastaveni VS Code

CP_ENTRY = "code.py"            # hlavni program CircuitPythonu
MP_ENTRY = "main.py"            # hlavni program MicroPythonu

DRIVE_LABEL = "CIRCUITPY"       # jmeno USB disku desky s CircuitPythonem
BOOT_LABEL = "RPI-RP2"          # jmeno disku RP2040 v rezimu bootloaderu (BOOTSEL)
BAUD = 115200                   # u USB serioveho portu na rychlosti nezalezi

# Kazde USB zarizeni ma dve cisla: VID (vyrobce) a PID (vyrobek).
# Podle nich pozname, o jakou desku jde. Tabulka MicroPython desek je
# prevzata z puvodniho utils.ps1.
CP_DEVICES = [
    (0x2E8A, 0x1026, "ELECFREAKS Pico:ed (CircuitPython)"),
]
MP_DEVICES = [
    (0x2E8A, 0x000A, "ELECFREAKS Pico:ed (MicroPython)"),
    (0x2E8A, 0x0005, "Raspberry Pi Pico / Pico W (MicroPython)"),
    (0x303A, 0x1001, "ESP32-S2 (MicroPython)"),
    (0x303A, 0x1002, "ESP32-S3 (MicroPython)"),
    (0x303A, 0x1003, "ESP32-C3 (MicroPython)"),
    (0x303A, 0x1004, "ESP32-C6 (MicroPython)"),
    (0x303A, 0x1005, "ESP32-H2 (MicroPython)"),
    (0x2886, 0x0046, "Seeed XIAO RP2040 (MicroPython)"),
    (0x239A, 0x00F1, "Adafruit Feather RP2040 (MicroPython)"),
    (0x0D28, 0x0204, "BBC micro:bit (MicroPython)"),
]

# Co se na CircuitPython desku nikdy nenahraje, i kdyby to v .ignoreCopy
# chybelo. Vse ostatni urcuje .vscode/.ignoreCopy (jedno misto pro Ctrl+S
# i pro "cpy upload").
SKIP_DIRS = {"__pycache__"}
SKIP_FILES = ["*.pyc", "boot_out.txt"]
# Systemove polozky na disku CIRCUITPY - nevypisuji se a nemazou.
SYSTEM_ENTRIES = {"System Volume Information", ".fseventsd", ".Trashes", ".Trash-1000",
                  ".metadata_never_index", "boot_out.txt"}

# Prepinace pomoci promennych prostredi (nepovinne):
#   CPY_DEBUG=1        vypisuje vsechno, co jde po seriove lince
#   CIRCUITPY_PORT     port CircuitPython desky (jinak automaticky)
#   CIRCUITPY_PATH     disk CircuitPython desky (jinak automaticky)
#   MICROPYTHON_PORT   port MicroPython desky (jinak automaticky)
#   NO_COLOR=1         bez barev
DEBUG = bool(os.environ.get("CPY_DEBUG"))
IS_WIN = sys.platform == "win32"

# Virtualni prostredi projektu s knihovnami (vytvari ho setup.bat / setup.sh).
VENV_DIR = PROJECT / ".venv"
VENV_PY = VENV_DIR / ("Scripts/python.exe" if IS_WIN else "bin/python")
SETUP_HINT = "spust setup.bat (Windows) nebo ./setup.sh (Linux, macOS) - nainstaluje knihovny do .venv"
# Python pro nastroje spoustene jako samostatny proces (mpremote, circup).
# use_venv() ho prepne na Python z .venv.
TOOL_PY = sys.executable


def pip_cmd(name):
    """Prikaz pro rucni instalaci knihovny (do .venv, kdyz existuje)."""
    if VENV_PY.exists():
        py = r".venv\Scripts\python" if IS_WIN else ".venv/bin/python"
    else:
        py = "python" if IS_WIN else "python3"
    return f"{py} -m pip install {name}"


def missing_lib(name, what=""):
    """Chyba pro chybejici Python knihovnu - s radou, jak ji ziskat."""
    return CpyError(f"Chybi knihovna {name}{what}: {SETUP_HINT}\n"
                    f"       (rucne: {pip_cmd(name)})")


def _same_path(a, b):
    try:
        return Path(a).resolve() == Path(b).resolve()
    except OSError:
        return False


def use_venv():
    """Zpristupni knihovny z .venv projektu (mpremote, pyserial, matplotlib).
    Bez .venv nedela nic.

    Bezny pripad: .venv vzniklo ze stejneho Pythonu, jaky prave bezi - pak
    staci pridat jeho slozku site-packages do sys.path (rychle, zadny dalsi
    proces). Jinak (jiny Python nez ten, ze ktereho .venv vzniklo) se
    deska.py spusti znovu Pythonem z .venv."""
    global TOOL_PY
    if not VENV_PY.exists() or _same_path(sys.prefix, VENV_DIR):
        return                                  # bez .venv, nebo uz bezime v nem
    home = None
    with contextlib.suppress(OSError):
        for row in (VENV_DIR / "pyvenv.cfg").read_text(encoding="utf-8").splitlines():
            key, _, value = row.partition("=")
            if key.strip() == "home":
                home = value.strip()
    if IS_WIN:
        site_dir = VENV_DIR / "Lib" / "site-packages"
    else:
        site_dir = VENV_DIR / "lib" / f"python{sys.version_info[0]}.{sys.version_info[1]}" / "site-packages"
    base_exe = getattr(sys, "_base_executable", None) or sys.executable
    if home and site_dir.is_dir() and _same_path(home, Path(base_exe).parent):
        import site
        site.addsitedir(str(site_dir))
        TOOL_PY = str(VENV_PY)
        return
    names = ("python.exe",) if IS_WIN else ("python3", "python")
    if not home or not any((Path(home) / n).exists() for n in names):
        # Python, ze ktereho .venv vzniklo, uz neexistuje (odinstalovany,
        # aktualizovany) - .venv nejde spustit. Pokracuje se bez nej.
        print(f"Upozorneni: virtualni prostredi .venv nejde pouzit, {SETUP_HINT}.", file=sys.stderr)
        return
    run_in_venv()


def run_in_venv():
    """Spusti deska.py znovu Pythonem z .venv a skonci s jeho navratovym
    kodem. Kdyz .venv nejde spustit, pokracuje se bez nej."""
    if os.environ.get("DESKA_VENV"):
        return
    env = dict(os.environ, DESKA_VENV="1")  # pojistka proti zacykleni
    args = [str(VENV_PY), str(Path(__file__).resolve()), *sys.argv[1:]]
    if not IS_WIN:
        try:
            os.execve(args[0], args, env)   # nahradi tento proces
        except OSError:
            return                          # rozbite .venv - pokracuj bez nej
    try:
        child = subprocess.Popen(args, env=env)
    except OSError:
        return
    while True:                             # Ctrl+C patri detskemu procesu (REPL, graf)
        try:
            sys.exit(child.wait())
        except KeyboardInterrupt:
            continue


# ============================================================
# ODDIL 2  Vypis na obrazovku (barvy, hlasky)
# ============================================================
def _setup_console():
    """Pripravi konzoli: neznamy znak nezpusobi padek a ve Windows
    zapne barevne (ANSI) sekvence."""
    with contextlib.suppress(Exception):
        sys.stdout.reconfigure(errors="replace")
        sys.stderr.reconfigure(errors="replace")
    if IS_WIN:
        with contextlib.suppress(Exception):
            import ctypes
            k = ctypes.windll.kernel32
            for std in (-11, -12):                      # stdout, stderr
                h = k.GetStdHandle(std)
                mode = ctypes.c_uint32()
                if k.GetConsoleMode(h, ctypes.byref(mode)):
                    k.SetConsoleMode(h, mode.value | 0x0004)   # VT sekvence


_setup_console()
USE_COLOR = sys.stdout.isatty() and not os.environ.get("NO_COLOR")
# Stejne barevne profily jako mely puvodni PowerShell skripty.
COLORS = {"info": "96", "error": "91", "file": "93", "dir": "95",
          "size": "90", "done": "92", "warn": "33"}


def col(text, kind):
    """Obarvi text (jen kdyz vystup jde do terminalu)."""
    if not USE_COLOR:
        return str(text)
    return f"\x1b[{COLORS[kind]}m{text}\x1b[0m"


def say(text="", kind=None):
    print(col(text, kind) if kind else text, flush=True)


def warn(text):
    print(col("POZOR", "warn") + ": " + text, flush=True)


def line(ch="-"):
    print(ch * 38, flush=True)


def write_raw(data):
    """Vypise bajty z desky tak, jak prisly (vcetne ceskych znaku v UTF-8)."""
    if data:
        sys.stdout.flush()
        sys.stdout.buffer.write(data)
        sys.stdout.buffer.flush()


def fmt_size(n):
    """Velikost citelne: B, kB, MB, GB."""
    for unit, size in (("GB", 1024 ** 3), ("MB", 1024 ** 2), ("kB", 1024)):
        if n >= size:
            return f"{n / size:.1f} {unit}"
    return f"{n} B"


class CpyError(Exception):
    """Ocekavana chyba (deska nenalezena, port obsazeny, ...).
    Hlavni funkce ji vypise jako 'ERROR: ...' bez dlouheho vypisu
    Pythonu a skonci s navratovym kodem 1."""


def stdin_is_console():
    """Je vstup opravdovy terminal, kde muze clovek psat?
    (Ve Windows hlasi isatty() True i pro zarizeni NUL, proto
    se navic overuje konzole pres GetConsoleMode.)"""
    if not sys.stdin or not sys.stdin.isatty():
        return False
    if IS_WIN:
        import ctypes
        import msvcrt
        mode = ctypes.c_uint32()
        return bool(ctypes.windll.kernel32.GetConsoleMode(
            msvcrt.get_osfhandle(sys.stdin.fileno()), ctypes.byref(mode)))
    return True


def confirm(question, opts):
    """Zepta se pred nevratnou akci. Volba --yes otazku preskoci."""
    if opts.has("yes"):
        return True
    if not stdin_is_console():
        raise CpyError("Potvrzeni vyzaduje interaktivni terminal (nebo pouzij volbu --yes).")
    try:
        ans = input(col(question, "warn") + " Napis 'ano' pro potvrzeni: ")
    except EOFError:
        ans = ""
    return ans.strip().lower() in ("ano", "a", "yes", "y")


class Steps:
    """Podrobny vypis po ocislovanych krocich.

    Pouzivaji ho prikazy, ktere student spousti z panelu nebo z Run on Save
    (upload, reset, repl, wipe, save), aby bylo videt, co se deje a KDE
    pripadne nastala chyba:

        Nahrani projektu na desku s MicroPythonem (09:22:58)
        --------------------------------------
        1) Co se nahrava
           soubor:      main.py (3003 B)
        2) Deska s MicroPythonem
           port:        COM4
        ...
        Hotovo: ...                      (nebo: ERROR: v kroku 2 - ... + rady)
    """

    def __init__(self, title):
        self.n = 0
        say(f"{title} ({time.strftime('%H:%M:%S')})")
        line()

    def head(self, text):
        """Zacatek dalsiho kroku."""
        self.n += 1
        say(f"{self.n}) {text}", "info")

    def info(self, label, value, kind=None):
        """Jeden udaj v kroku (zarovnany popisek a hodnota)."""
        value = str(value)
        say(f"   {label:<12} " + (col(value, kind) if kind else value))

    def fail(self, text, *tips):
        """Chyba v aktualnim kroku - ukonci prikaz s radami, co delat."""
        raise CpyError(f"v kroku {self.n} - {text}" + "".join(f"\n       - {t}" for t in tips))

    def done(self, text, kind="done"):
        """Zaverecna veta (uspech nebo ocekavany konec)."""
        line()
        say(text, kind)


@contextlib.contextmanager
def ctrl_c_to_child():
    """Behem interaktivniho programu (mpremote repl / run) nechame Ctrl+C
    jen jemu - jinak by Python tento skript ukoncil a REPL zabil."""
    old = signal.signal(signal.SIGINT, signal.SIG_IGN)
    try:
        yield
    finally:
        signal.signal(signal.SIGINT, old)


# ============================================================
# ODDIL 3  Hledani desek (USB disky, seriove porty)
# ============================================================
def find_drives(label):
    """Najde pripojene disky s danym jmenem (CIRCUITPY nebo RPI-RP2).
    Windows: projde pismena disku. macOS: /Volumes. Linux: /media, /run/media, /mnt."""
    if IS_WIN:
        return _win_drives(label)
    user = os.environ.get("USER", "")
    if sys.platform == "darwin":
        bases = [Path("/Volumes")]
    else:
        bases = [Path("/media") / user, Path("/run/media") / user, Path("/media"), Path("/mnt")]
    found = []
    for base in bases:
        with contextlib.suppress(OSError):
            for p in sorted(base.iterdir()):
                if (p.name == label or p.name.startswith(label + " ")) and p.is_dir() and p not in found:
                    found.append(p)
    return found


def _win_drives(label):
    """Windows: zjisti jmeno svazku u kazdeho mistniho disku. Sitove disky
    se preskakuji (jsou pomale), chybove okno 'vlozte disk' se potlaci."""
    import ctypes
    import string
    k = ctypes.windll.kernel32
    k.SetErrorMode(1)                                   # SEM_FAILCRITICALERRORS
    mask = k.GetLogicalDrives()
    found = []
    for i, letter in enumerate(string.ascii_uppercase):
        if not (mask >> i) & 1:
            continue
        root = f"{letter}:\\"
        if k.GetDriveTypeW(root) not in (2, 3):         # 2 = vymenny, 3 = pevny
            continue
        buf = ctypes.create_unicode_buffer(261)
        if k.GetVolumeInformationW(root, buf, 261, None, None, None, None, 0) \
                and buf.value.upper() == label:
            found.append(Path(root))
    return found


def wait_for(fn, timeout, step=0.5):
    """Opakovane vola fn(), dokud nevrati neco pravdiveho (nebo vyprsi cas)."""
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        res = fn()
        if res:
            return res
        time.sleep(step)
    return None


def list_ports():
    """Seznam seriovych portu (z knihovny pyserial)."""
    try:
        from serial.tools import list_ports as lp
    except ImportError:
        return []
    return list(lp.comports())


def known_name(port, table):
    """Vrati jmeno desky z tabulky podle VID:PID portu (nebo None)."""
    for vid, pid, name in table:
        if port.vid == vid and port.pid == pid:
            return name
    return None


def is_micropython_port(p):
    if known_name(p, MP_DEVICES):
        return True
    text = f"{p.description or ''} {p.product or ''} {p.manufacturer or ''}".lower()
    return "micropython" in text


def vidpid(p):
    return f"{p.vid:04X}:{p.pid:04X}" if p.vid is not None else "----:----"


def read_boot_out(drive):
    """Precte boot_out.txt z disku CIRCUITPY: verzi firmwaru, ID desky a UID.
    UID je stejne jako seriove cislo USB portu - tak se disk spari s portem."""
    info = {"line": "", "board_id": "", "uid": ""}
    with contextlib.suppress(OSError):
        text = (drive / "boot_out.txt").read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        info["line"] = lines[0].strip() if lines else ""
        m = re.search(r"Board ID:\s*(\S+)", text)
        info["board_id"] = m.group(1) if m else ""
        m = re.search(r"UID:\s*([0-9A-Fa-f]+)", text)
        info["uid"] = m.group(1).upper() if m else ""
    return info


def ports_for_uid(uid, ports=None):
    """Porty, jejichz USB seriove cislo je stejne jako UID z boot_out.txt.
    Prvni z nich je konzole (REPL)."""
    ports = list_ports() if ports is None else ports
    same = [p for p in ports if uid and (p.serial_number or "").upper() == uid]
    same.sort(key=lambda p: (p.location or "", p.device))
    return same


class Board:
    """Jedna deska s CircuitPythonem: jeji disk a seriovy port.
    Obe se hledaji az ve chvili, kdy je potreba (a jen jednou)."""

    def __init__(self, opts):
        self.opts = opts
        self._drive = None
        self._port = None

    # --- disk CIRCUITPY ---
    def drive_or_none(self):
        if self._drive:
            return self._drive
        if self.opts.drive:
            p = Path(self.opts.drive)
            if IS_WIN and re.fullmatch(r"[A-Za-z]:", self.opts.drive):
                p = Path(self.opts.drive + "\\")
            self._drive = p if p.is_dir() else None
            return self._drive
        drives = find_drives(DRIVE_LABEL)
        if len(drives) > 1:
            warn("Pripojeno vic desek CIRCUITPY: " + ", ".join(str(d) for d in drives)
                 + f". Pouzivam {drives[0]} (jinou vyberes volbou --drive).")
        self._drive = drives[0] if drives else None
        return self._drive

    @property
    def drive(self):
        d = self.drive_or_none()
        if d:
            return d
        if self.opts.drive:
            raise CpyError(f"Zadany disk '{self.opts.drive}' neexistuje.")
        raise CpyError("Disk CIRCUITPY nenalezen.\n" + why_no_circuitpy())

    def boot_info(self):
        d = self.drive_or_none()
        return read_boot_out(d) if d else {"line": "", "board_id": "", "uid": ""}

    # --- seriovy port ---
    def port_or_none(self):
        """Najde port v tomto poradi: volba --port, parovani podle UID z
        boot_out.txt, tabulka VID:PID, popis zarizeni obsahujici 'CircuitPython'."""
        if self._port:
            return self._port
        if self.opts.port:
            self._port = self.opts.port
            return self._port
        ports = list_ports()
        uid = self.boot_info()["uid"]
        same = ports_for_uid(uid, ports)
        if same:
            self._port = same[0].device
            return self._port
        known = [p for p in ports if known_name(p, CP_DEVICES)]
        if not known:
            known = [p for p in ports if "circuitpython" in (p.description or "").lower()
                     or "circuitpython" in (p.product or "").lower()]
        if len(known) == 1:
            self._port = known[0].device
        elif len(known) > 1 and not uid:
            raise CpyError("Pripojeno vic desek s CircuitPythonem: "
                           + ", ".join(p.device for p in known) + ". Vyber jednu volbou --port.")
        return self._port

    @property
    def port(self):
        p = self.port_or_none()
        if not p:
            raise CpyError("Seriovy port desky nenalezen. Je deska pripojena? (port lze zadat: --port COMx)")
        return p


def why_no_circuitpy():
    """Napovi, proc nebyl nalezen disk CIRCUITPY."""
    tips = []
    if find_drives(BOOT_LABEL):
        tips.append("Deska je v rezimu bootloaderu (disk RPI-RP2): stiskni RESET, "
                    "nebo nahraj firmware: cpy flash <soubor.uf2>.")
    for p in list_ports():
        if is_micropython_port(p):
            tips.append(f"Na {p.device} je deska s MicroPythonem - na tu pouzij mpy.")
    tips.append("Je deska pripojena DATOVYM kabelem a je na ni CircuitPython?")
    return "\n".join("       - " + t for t in tips)


# ============================================================
# ODDIL 4  Seriova konzole desky (REPL a raw REPL)
# ============================================================
# Jak se s deskou "mluvi" po seriove lince (MicroPython i CircuitPython
# to maji stejne):
#   Ctrl+C (0x03)  prerusi bezici program
#   Ctrl+D (0x04)  v REPL: mekky restart (znovu spusti code.py / main.py)
#   Ctrl+A (0x01)  prepne do "raw REPL" - rezimu pro programy: posle se
#                  kod, Ctrl+D ho spusti, deska odpovi "OK", vystup programu,
#                  znak 0x04, chybovy vystup, znak 0x04 a vyzvu ">"
#   Ctrl+B (0x02)  zpet z raw REPL do normalniho REPL (vyzva ">>> ")
# CircuitPython navic posila sekvence ESC ] 0 ; ... ESC \  - meni jimi
# titulek terminalu. Do vystupu nepatri, proto je filtrujeme.
_OSC_RE = re.compile(rb"\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)")    # titulek terminalu
_CSI_RE = re.compile(rb"\x1b\[[0-9;?]*[A-Za-z]")              # pohyb kurzoru, mazani radku


class OscFilter:
    """Odfiltruje sekvence pro titulek terminalu. Data chodi po kouscich,
    proto si nedokoncenou sekvenci podrzi do dalsiho volani."""

    def __init__(self):
        self.buf = b""

    def feed(self, data):
        data = _OSC_RE.sub(b"", self.buf + data)
        self.buf = b""
        i = data.rfind(b"\x1b]")                         # zacatek nedokoncene sekvence
        if i == -1 and data.endswith(b"\x1b"):
            i = len(data) - 1
        if i != -1 and len(data) - i < 256:
            self.buf, data = data[i:], data[:i]
        return data


class Repl:
    """Spojeni se seriovou konzoli desky (pouziva cpy; mpy ma mpremote)."""

    def __init__(self, port):
        try:
            import serial
        except ImportError:
            raise missing_lib("pyserial")
        try:
            self.ser = serial.Serial(port, BAUD, timeout=0.05, write_timeout=2)
        except (serial.SerialException, OSError) as e:
            raise CpyError(f"Port {port} nelze otevrit: {e}\n"
                           "       - neni otevreny REPL / Serial Monitor / graf v jinem okne?")
        self.port = port
        self.rx = bytearray()           # prijata a jeste nezpracovana data

    def close(self):
        with contextlib.suppress(Exception):
            self.ser.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    # --- cteni a zapis ---
    def write(self, data):
        if DEBUG:
            sys.stderr.write(f"[tx] {data!r}\n")
        self.ser.write(data)

    def _fill(self):
        chunk = self.ser.read(self.ser.in_waiting or 1)
        if chunk:
            if DEBUG:
                sys.stderr.write(f"[rx] {chunk!r}\n")
            self.rx += chunk
        return chunk

    def _take(self, n=None):
        n = len(self.rx) if n is None else n
        data = bytes(self.rx[:n])
        del self.rx[:n]
        return data

    def read_until(self, marker, timeout):
        """Cte, dokud neprijde text 'marker'. Vraci (nalezeno, data)."""
        end = time.monotonic() + timeout
        while True:
            i = self.rx.find(marker)
            if i >= 0:
                return True, self._take(i + len(marker))
            if time.monotonic() > end:
                return False, self._take()
            self._fill()

    def read_for(self, seconds):
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            self._fill()
        return self._take()

    # --- stavy desky ---
    def interrupt(self):
        """Zastavi program a dostane desku do REPL (vyzva '>>> ').
        Postup: Ctrl+C (zastavit), Ctrl+B (z raw REPL ven, nebo 'stisk
        libovolne klavesy' po skonceni programu). Zkusi to az 3x."""
        self.ser.reset_input_buffer()
        self.rx.clear()
        got = b""
        for attempt in range(3):
            self.write(b"\r\x03")
            time.sleep(0.1)
            self.write(b"\x03")
            got += self.read_for(0.4)
            self.write(b"\x02")
            ok, data = self.read_until(b">>> ", 2 + attempt)
            got += data
            if ok:
                got += self.read_for(0.15)      # dalsi vyzvy, ktere jeste dobehly
                return got
        raise CpyError("Deska neodpovida v REPL (zkus odpojit a pripojit USB kabel).")

    def soft_reload(self):
        """Z REPL znovu spusti code.py (Ctrl+D)."""
        self.write(b"\x04")
        ok, _ = self.read_until(b"soft reboot", 3)
        return ok

    def enter_raw(self):
        self.write(b"\x01")
        ok, _ = self.read_until(b"raw REPL; CTRL-B to exit\r\n>", 3)
        if not ok:
            raise CpyError("Deska nepresla do raw REPL.")

    def exit_raw(self):
        self.write(b"\x02")
        self.read_until(b">>> ", 2)

    def raw_send(self, code):
        """Posle kod v raw REPL (po 256 bajtech, aby deska stihala) a spusti ho."""
        data = code.encode("utf-8")
        for i in range(0, len(data), 256):
            self.write(data[i:i + 256])
            time.sleep(0.01)
        self.write(b"\x04")
        ok, _ = self.read_until(b"OK", 3)
        if not ok:
            raise CpyError("Deska neprijala kod v raw REPL.")

    def raw_section(self, on_data=None, timeout=10.0):
        """Cte vystup az po znak 0x04 (konec stdout nebo stderr).
        on_data dostava data prubezne (pro zive vypisovani)."""
        out = bytearray()
        end = None if timeout is None else time.monotonic() + timeout
        while True:
            i = self.rx.find(b"\x04")
            part = self._take(i if i >= 0 else None)
            if i >= 0:
                del self.rx[:1]
            if part:
                out += part
                if on_data:
                    on_data(part)
            if i >= 0:
                return bytes(out)
            if end is not None and time.monotonic() > end:
                raise CpyError("Deska neodpovedela vcas.")
            self._fill()

    def raw_collect(self, on_out=None, timeout=10.0):
        out = self.raw_section(on_out, timeout)
        err = self.raw_section(None, 10.0 if timeout is None else timeout)
        self.read_until(b">", 1)
        return out, err

    def run_snippet(self, code, timeout=10.0):
        """Spusti kratky kod v raw REPL a vrati jeho vystup jako text."""
        self.enter_raw()
        try:
            self.raw_send(code)
            out, err = self.raw_collect(None, timeout)
        finally:
            self.exit_raw()
        if err.strip():
            raise CpyError("Chyba na desce:\n" + err.decode("utf-8", "replace").strip())
        return out.decode("utf-8", "replace")

    def fire_and_forget(self, code):
        """Spusti kod, po kterem se deska restartuje (spojeni zanikne)."""
        self.enter_raw()
        self.write(code.encode("utf-8") + b"\x04")
        with contextlib.suppress(Exception):
            self.read_for(0.5)
        self.close()


def terminal(ser, on_exit_hint=""):
    """Jednoduchy terminal: co prijde z desky, vypise; co napises, posle.
    Konec: Ctrl+].  Ctrl+C se posila do desky (prerusi program)."""
    stop = threading.Event()
    lost = []
    flt = OscFilter()
    WIN_KEYS = {"H": b"\x1b[A", "P": b"\x1b[B", "M": b"\x1b[C", "K": b"\x1b[D",
                "G": b"\x1b[H", "O": b"\x1b[F", "S": b"\x1b[3~"}     # sipky, Home, End, Del

    def reader():
        while not stop.is_set():
            try:
                data = ser.read(ser.in_waiting or 1)
            except Exception as e:              # noqa: BLE001 - odpojena deska
                lost.append(e)
                stop.set()
                break
            write_raw(flt.feed(data))

    t = threading.Thread(target=reader, daemon=True)
    t.start()
    try:
        if IS_WIN:
            import msvcrt
            while not stop.is_set():
                try:
                    if not msvcrt.kbhit():
                        time.sleep(0.01)
                        continue
                    ch = msvcrt.getwch()
                except KeyboardInterrupt:
                    ser.write(b"\x03")
                    continue
                if ch == "\x1d":                # Ctrl+]
                    break
                if ch in ("\x00", "\xe0"):      # specialni klavesa (sipka, ...)
                    seq = WIN_KEYS.get(msvcrt.getwch())
                    if seq:
                        ser.write(seq)
                    continue
                ser.write(ch.encode("utf-8"))
        else:
            import select
            import termios
            import tty
            fd = sys.stdin.fileno()
            old = termios.tcgetattr(fd)
            tty.setraw(fd)
            try:
                while not stop.is_set():
                    r, _, _ = select.select([fd], [], [], 0.05)
                    if r:
                        data = os.read(fd, 64)
                        if b"\x1d" in data:
                            break
                        ser.write(data)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old)
    finally:
        stop.set()
        t.join(0.5)
    if lost:
        raise CpyError(f"Spojeni s deskou bylo preruseno: {lost[0]}")


# ============================================================
# ODDIL 5  Soubory projektu (.ignoreCopy) a stromovy vypis
# ============================================================
def load_ignore():
    """Nacte masky z .vscode/.ignoreCopy (jedna maska na radek).
    '*' odpovida libovolnemu textu vcetne '/', '**' znamena totez."""
    patterns = []
    with contextlib.suppress(OSError):
        for raw in IGNORE_FILE.read_text(encoding="utf-8-sig").splitlines():
            p = raw.strip().replace("\\", "/")
            if p and not p.startswith("#"):
                patterns.append(p.replace("**", "*"))
    return patterns


def skip_reason(rel, patterns, is_dir=False):
    """Proc se polozka projektu (relativni cesta s '/') NEnahrava?
    Vraci text duvodu, nebo None, kdyz se nahrava."""
    parts = rel.split("/")
    for part in parts:
        if part.startswith("."):
            return "skryta polozka"
        if part in SKIP_DIRS:
            return part
    if not is_dir and any(fnmatch.fnmatch(parts[-1], s) for s in SKIP_FILES):
        return parts[-1]
    probe = rel + "/__cpy_dir__" if is_dir else rel      # u slozky testujeme jeji obsah
    for p in patterns:
        if fnmatch.fnmatch(probe, p):
            return f"maska '{p}' v .ignoreCopy"
    return None


def project_files():
    """Soubory projektu, ktere patri na CircuitPython desku (relativni
    cesty s '/'). Poradi: knihovny v lib/, ostatni soubory, code.py
    nakonec - aby se program spustil az se vsim, co potrebuje."""
    patterns = load_ignore()
    files = []
    for root, dirs, names in os.walk(PROJECT):
        rel_root = Path(root).relative_to(PROJECT).as_posix()
        rel_root = "" if rel_root == "." else rel_root + "/"
        dirs[:] = sorted(d for d in dirs if not skip_reason(rel_root + d, patterns, is_dir=True))
        for n in sorted(names):
            if not skip_reason(rel_root + n, patterns):
                files.append(rel_root + n)
    files.sort(key=lambda r: (r == CP_ENTRY, not r.startswith("lib/"), r.lower()))
    return files


# BOM (Byte Order Mark) jsou 3 neviditelne bajty na zacatku souboru, ktere
# nekdy prida Poznamkovy blok nebo PowerShell ("UTF-8 with BOM"). MicroPython
# ani CircuitPython je neznaji a program spadne hned na 1. radku chybou
#     NameError: name '\ufeff' is not defined
# Ve VS Code se kodovani prepne vpravo dole v liste: klik na "UTF-8 with BOM"
# -> "Save with Encoding" -> "UTF-8".
UTF8_BOM = b"\xef\xbb\xbf"
BOM_HELP = ("ve VS Code klikni vpravo dole na 'UTF-8 with BOM' -> "
            "'Save with Encoding' -> 'UTF-8'")


def has_bom(path):
    try:
        with open(path, "rb") as f:
            return path.suffix.lower() == ".py" and f.read(3) == UTF8_BOM
    except OSError:
        return False


def board_bytes(src):
    """Obsah souboru tak, jak patri na desku: u .py bez BOM."""
    data = src.read_bytes()
    if src.suffix.lower() == ".py" and data.startswith(UTF8_BOM):
        data = data[len(UTF8_BOM):]
    return data


def same_content(src, dst):
    """Ma soubor na desce stejny obsah jako v projektu?"""
    try:
        return board_bytes(src) == dst.read_bytes()
    except OSError:
        return False


def copy_file(src, dst, announce_bom=True):
    """Zkopiruje soubor na desku a pocka, az ho system opravdu zapise (fsync).
    U .py souboru odstrani BOM (viz vyse) a upozorni na to
    (announce_bom=False: upozorneni uz vypsal podrobny vypis Steps)."""
    if announce_bom and has_bom(src):
        warn(f"{src.name} je ulozeny jako 'UTF-8 with BOM' - na desku ho nahravam bez BOM "
             f"({BOM_HELP}).")
    dst.parent.mkdir(parents=True, exist_ok=True)
    with open(dst, "wb") as fo:
        fo.write(board_bytes(src))
        fo.flush()
        os.fsync(fo.fileno())
    with contextlib.suppress(OSError):
        shutil.copystat(src, dst)


# Strom souboru je slovnik {"files": [(jmeno, velikost)], "dirs": [(jmeno, strom)]}.
# Umime ho postavit z disku (CircuitPython) i z vypisu desky (MicroPython)
# a vypsat ho stejne.
def tree_from_disk(path):
    node = {"files": [], "dirs": [], "error": None}
    try:
        entries = [e for e in path.iterdir() if e.name not in SYSTEM_ENTRIES]
    except OSError as e:
        node["error"] = str(e)
        return node
    for e in sorted(entries, key=lambda e: e.name.lower()):
        if e.is_dir():
            node["dirs"].append((e.name, tree_from_disk(e)))
        else:
            node["files"].append((e.name, e.stat().st_size))
    return node


def tree_chars():
    """Znaky pro kresleni stromu (kdyz konzole neumi Unicode, tak ASCII)."""
    try:
        "\u251c\u2500\u2514\u2502".encode(sys.stdout.encoding or "ascii")
        return "\u251c\u2500\u2500 ", "\u2514\u2500\u2500 ", "\u2502   ", "    "
    except (UnicodeEncodeError, LookupError):
        return "|-- ", "`-- ", "|   ", "    "


def print_tree(node):
    """Vypise strom: nejdriv soubory (s velikosti), pak slozky. Vraci statistiku."""
    mid, last, keep, skip = tree_chars()
    stats = {"files": 0, "bytes": 0}

    def walk(n, prefix):
        if n.get("error"):
            say(prefix + col(f"(nelze cist: {n['error']})", "error"))
        files, dirs = n["files"], n["dirs"]
        for i, (name, size) in enumerate(files):
            br = last if (i == len(files) - 1 and not dirs) else mid
            stats["files"] += 1
            stats["bytes"] += size
            gap = " " * max(1, 40 - len(prefix + br + name))
            print(prefix + br + col(name, "file") + gap + "(" + col(f"{size:6d} B", "size") + ")")
        for i, (name, sub) in enumerate(dirs):
            is_last = i == len(dirs) - 1
            print(prefix + (last if is_last else mid) + col(name + "/", "dir"))
            walk(sub, prefix + (skip if is_last else keep))

    walk(node, "")
    return stats


# ============================================================
# ODDIL 6  Spolecne prikazy (devices, vscode, graf)
# ============================================================
def collect_devices():
    """Zjisti vsechny pripojene desky. Nic do nich neposila a seriove porty
    neotevira (programy na deskach bezi dal, REPL v jinem okne nevadi).
    Vraci seznam slovniku - stejna data pouziva vypis pro cloveka
    i vystup --json pro panel ve VS Code."""
    ports = list_ports()
    used = set()
    devices = []
    for d in find_drives(DRIVE_LABEL):
        info = read_boot_out(d)
        same = ports_for_uid(info["uid"], ports)
        used.update(p.device for p in same)
        devices.append({
            "platform": "circuitpython", "tool": "cpy",
            "port": same[0].device if same else None, "drive": str(d),
            "name": info["line"].split(";")[-1].strip() if ";" in info["line"] else info["board_id"],
            "firmware": info["line"].split(";")[0].strip() if info["line"] else None,
            "note": None if same else "seriovy port nenalezen",
        })
    for p in ports:
        if p.device not in used and known_name(p, CP_DEVICES):
            used.add(p.device)
            devices.append({
                "platform": "circuitpython", "tool": "cpy", "port": p.device, "drive": None,
                "name": known_name(p, CP_DEVICES), "firmware": None,
                "note": "disk CIRCUITPY nenalezen (vypnuty v boot.py?)",
            })
    for p in ports:
        if p.device not in used and is_micropython_port(p):
            used.add(p.device)
            devices.append({
                "platform": "micropython", "tool": "mpy", "port": p.device, "drive": None,
                "name": known_name(p, MP_DEVICES) or p.description, "firmware": None,
                "note": None, "usb": vidpid(p),
            })
    for d in find_drives(BOOT_LABEL):
        devices.append({
            "platform": "bootloader", "tool": "cpy", "port": None, "drive": str(d),
            "name": "deska v rezimu bootloaderu (RPI-RP2)", "firmware": None,
            "note": "nahraj firmware (cpy flash <soubor.uf2>) nebo stiskni RESET",
        })
    for p in ports:
        if p.device not in used and p.vid is not None:
            devices.append({
                "platform": "other", "tool": None, "port": p.device, "drive": None,
                "name": p.description, "firmware": None, "note": None, "usb": vidpid(p),
            })
    return devices


def cmd_devices(opts):
    """Vypise vsechny pripojene desky a ke kazde rekne, ktery nastroj pouzit.
    S volbou --json vypise totez jako JSON (cte ho panel ve VS Code)."""
    devices = collect_devices()
    if opts.has("json"):
        print(json.dumps({"version": 1, "devices": devices}, ensure_ascii=False))
        return
    sections = [
        ("circuitpython", "CircuitPython  (prikazy cpy)"),
        ("micropython", "MicroPython  (prikazy mpy)"),
        ("bootloader", "Rezim bootloaderu (nahrani firmwaru .uf2)"),
        ("other", "Ostatni USB seriova zarizeni (nejsou desky z kurzu)"),
    ]
    for platform, title in sections:
        items = [d for d in devices if d["platform"] == platform]
        if not items and platform in ("bootloader", "other"):
            continue
        say(title, "info")
        for d in items:
            where = f"{d['port'] or '':<8} " + (f"disk {d['drive']}   " if d["drive"] else "")
            text = d["firmware"] + "; " + d["name"] if d["firmware"] else d["name"]
            extra = f"   (USB {d['usb']})" if d.get("usb") else ""
            say(f"   {where}{text}{extra}" + (f"  - {d['note']}" if d["note"] else ""))
        if not items:
            say("   zadna")
    line()
    if not any(d["platform"] != "other" for d in devices):
        say("Neni pripojena zadna deska. Pouzij DATOVY USB kabel.", "warn")


# Tlacitka panelu "MicroPython & CircuitPython Panel" a stavoveho radku.
# Panel je RYCHLY PRISTUP k zakladnim akcim, ne kopie vsech prikazu CLI -
# ostatni prikazy jsou v terminalu (mpy help, cpy help).
# Panel jen vlozi text "command" do terminalu, proto staci obycejny
# prikazovy radek. {py} se nahradi za "python" (Windows) nebo "python3".
#   name      text ve stavovem radku; $(ikona) je ikona VS Code (codicon)
#   label     text tlacitka v panelu (blok uz rika, o kterou platformu jde)
#   group     blok v panelu; platform = ktere desky blok ukazuje a kdy se
#             ztlumi (kdyz takova deska neni pripojena)
#   statusBar False = tlacitko jen v panelu, ne ve spodnim stavovem radku
#   confirm   (nepovinne, 8. polozka) otazka v dialogu VS Code pred spustenim;
#             pro nevratne akce - prikaz pak ma --yes, terminal se uz nepta
_MPY, _CPY = ("MicroPython", "micropython"), ("CircuitPython", "circuitpython")
_WIPE_MPY = "Smazat V\u0160ECHNY soubory na desce s MicroPythonem? Operace je nevratn\u00e1."
_WIPE_CPY = "Smazat V\u0160ECHNY soubory na disku CIRCUITPY? Operace je nevratn\u00e1."
PANEL_BUTTONS = [
    # id           stavovy radek                  panel                          prikaz        barva        blok  stav.radek
    ("mpy-upload", "$(cloud-upload) MPY Upload",  "\u2b06  Nahr\u00e1t projekt", "mpy upload", "yellow",     _MPY, True),
    ("mpy-run",    "$(play) MPY Run",             "\u25b6  Spustit main.py",     "mpy reset",  "lightgreen", _MPY, False),
    ("mpy-repl",   "$(terminal) MPY REPL",        "\u2328  Konzole (REPL)",      "mpy repl",   "lightblue",  _MPY, True),
    ("mpy-wipe",   "$(trash) MPY Wipe",           "\U0001f5d1  Smazat desku",    "mpy wipe --yes", "red",  _MPY, False, _WIPE_MPY),
    ("cpy-upload", "$(cloud-upload) CPY Upload",  "\u2b06  Nahr\u00e1t projekt", "cpy upload", "yellow",     _CPY, True),
    ("cpy-reset",  "$(debug-restart) CPY Restart", "\u21bb  Restartovat program", "cpy reset", "lightgreen", _CPY, False),
    ("cpy-repl",   "$(terminal) CPY REPL",        "\u2328  Konzole (REPL)",      "cpy repl",   "lightblue",  _CPY, True),
    ("cpy-wipe",   "$(trash) CPY Wipe",           "\U0001f5d1  Smazat desku",    "cpy wipe --yes", "red",  _CPY, False, _WIPE_CPY),
]
# Run on Save: po ulozeni souboru s touto priponou se zavola "cpy save".
# Ktere soubory se opravdu zkopiruji, rozhodne .vscode/.ignoreCopy.
RUN_ON_SAVE_MATCH = r"\.(py|toml|json|txt|csv)$"


def cmd_vscode(opts):
    """Zapise do .vscode/settings.json tlacitka panelu a Run on Save pro
    tento operacni system. Ostatni nastaveni v souboru zustanou."""
    py = "python" if IS_WIN else "python3"
    try:
        data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8-sig")) if SETTINGS_FILE.exists() else {}
    except ValueError as e:
        raise CpyError(f"{SETTINGS_FILE} neni platny JSON: {e}")
    before = json.dumps(data, sort_keys=True)
    data["emeraldwalk.runonsave"] = {"commands": [{
        "match": RUN_ON_SAVE_MATCH,
        "isAsync": True,
        "cmd": py + ' "${workspaceFolder}/.vscode/deska.py" cpy save "${relativeFile}"',
    }]}
    buttons = []
    for bid, name, label, cmd, color, (group, platform), status_bar, *rest in PANEL_BUTTONS:
        b = {"id": bid, "name": name, "label": label, "command": f"{py} .vscode/deska.py {cmd}",
             "color": color, "group": group, "platform": platform}
        if not status_bar:
            b["statusBar"] = False
        if rest:                                # potvrzeni v dialogu VS Code
            b["confirm"] = rest[0]
            b["confirmButton"] = "Smazat"
        buttons.append(b)
    data["micropython.commands"] = buttons
    # Panel si sam (kdyz je videt) zjistuje pripojene desky timto prikazem.
    data["micropython.devicesCommand"] = f"{py} .vscode/deska.py devices --json"
    data.setdefault("micropython.enableStatusToolbar", True)
    # Na Windows uz settings.json z gitu obsahuje presne tohle (prikazy "python"),
    # takze se nic nemeni a okno neni potreba znovu nacitat. Na Linuxu/macOS se
    # prepise "python" na "python3" - panel pak sam nabidne "Prenacist okno".
    changed = json.dumps(data, sort_keys=True) != before
    if changed:
        SETTINGS_FILE.write_text(json.dumps(data, indent=4, ensure_ascii=False) + "\n", encoding="utf-8")
        say(f"Nastaveni zapsano: {SETTINGS_FILE}", "done")
    else:
        say(f"Nastaveni uz je aktualni: {SETTINGS_FILE}", "done")
    say(f"   Run on Save: soubory {RUN_ON_SAVE_MATCH} -> cpy save (podle .ignoreCopy)")
    say(f"   Panel: bloky MicroPython a CircuitPython, {len(buttons)} tlacitek, z toho "
        f"{sum(1 for b in PANEL_BUTTONS if b[6])} ve stavovem radku ({py} .vscode/deska.py ...)")
    say("   Bloky ukazuji pripojene desky (devices --json).")
    if changed:
        say("   Tlacitka se zmenila. Pokud uz je panel nainstalovany, nabidne 'Prenacist okno'")
        say("   (nebo F1 -> 'Developer: Reload Window'). Panel nainstalovany az potom je nacte sam.")


def parse_values(text):
    """Z radku typu '1.5, 20, 30' nebo '(1.5, 20, 30)' udela seznam cisel.
    Kdyz radek neni seznam cisel (napr. bezny vypis), vrati None."""
    text = text.strip().strip("()[]")
    if not text:
        return None
    try:
        return [float(v) for v in re.split(r"[,;\s]+", text) if v]
    except ValueError:
        return None


class SeriesBuffer:
    """Posledni hodnoty pro graf. Prvni cislo na radku je osa X (napr. cas),
    dalsi cisla jsou krivky. Kdyz je na radku jen jedno cislo, osa X je
    poradove cislo mereni."""

    def __init__(self, max_points=500):
        self.x = deque(maxlen=max_points)
        self.ys = []
        self.max_points = max_points
        self.count = 0

    def add(self, values):
        if len(values) == 1:
            x, ys = float(self.count), values
        else:
            x, ys = values[0], values[1:]
        self.count += 1
        while len(self.ys) < len(ys):                       # nova krivka
            self.ys.append(deque([float("nan")] * len(self.x), maxlen=self.max_points))
        self.x.append(x)
        for i, series in enumerate(self.ys):
            series.append(ys[i] if i < len(ys) else float("nan"))


def run_plotter(port, title, seconds=None):
    """Zivy graf hodnot, ktere program na desce vypisuje pres print().
    Na desce staci treba:   print(time.monotonic(), vzdalenost, rychlost)
    seconds: graf se po zadane dobe sam zavre (pouziva se pri testech)."""
    try:
        import matplotlib.pyplot as plt
        from matplotlib.animation import FuncAnimation
    except ImportError:
        raise missing_lib("matplotlib", " (graf)")
    try:
        import serial
        ser = serial.Serial(port, BAUD, timeout=0)
    except ImportError:
        raise missing_lib("pyserial")
    except (serial.SerialException, OSError) as e:
        raise CpyError(f"Port {port} nelze otevrit: {e}\n"
                       "       - neni otevreny REPL / Serial Monitor v jinem okne?")
    say(f"Graf z portu {port}. Na desce vypisuj cisla oddelena carkou, napr. print(t, a, b).", "info")
    say("Zavreni: zavri okno grafu.", "info")
    buf = SeriesBuffer()
    flt = OscFilter()
    state = {"pending": b""}
    fig, ax = plt.subplots()
    with contextlib.suppress(Exception):
        fig.canvas.manager.set_window_title(title)
    ax.grid(True)
    lines = []

    def update(_frame):
        try:
            waiting = ser.in_waiting
            data = ser.read(waiting) if waiting else b""
        except Exception:                       # noqa: BLE001 - deska odpojena
            plt.close(fig)
            return lines
        rows = (state["pending"] + _CSI_RE.sub(b"", flt.feed(data))).split(b"\n")
        state["pending"] = rows.pop()           # posledni radek jeste neni cely
        for raw in rows:
            values = parse_values(raw.decode("utf-8", "replace"))
            if values:
                buf.add(values)
        while len(lines) < len(buf.ys):
            lines.append(ax.plot([], [], lw=2, label=f"hodnota {len(lines) + 1}")[0])
            ax.legend(loc="upper left")
        for ln, series in zip(lines, buf.ys):
            ln.set_data(list(buf.x), list(series))
        if buf.x:
            ax.relim()
            ax.autoscale_view()
        return lines

    anim = FuncAnimation(fig, update, interval=50, cache_frame_data=False)  # noqa: F841 - musi zit
    if seconds:
        timer = fig.canvas.new_timer(interval=int(seconds * 1000))
        timer.add_callback(plt.close, fig)
        timer.start()
    try:
        plt.show()
    finally:
        ser.close()
    say(f"Graf zavren. Prijato mereni: {buf.count}", "done")
    return buf


# ============================================================
# ODDIL 7  CircuitPython - prikazy cpy
# ============================================================
# Jak CircuitPython spousti program:
#   - po startu nebo restartu spusti code.py (kdyz chybi, tak main.py)
#   - kdyz se na disk CIRCUITPY neco zapise, pocka, az zapisy na chvili
#     ustanou (asi 0,5 s), a program jednou restartuje (autoreload).
#     Proto se vic souboru zkopirovanych rychle za sebou nahraje s jedinym
#     restartem a program nikdy nebezi s napul nahranymi soubory.
_START_RE = re.compile(rb"(\w+\.py) output:")
_STATUS_LINES = ("Code done running.", "Press any key to enter the REPL", "Auto-reload is on",
                 "Code stopped by auto-reload")


class RestartWatcher:
    """Pasivne posloucha seriovou linku (nic neposila) a po zapisu na disk
    overi, ze autoreload program znovu spustil, a ukaze jeho prvni vystup.
    Kdyz je port obsazeny (napr. otevreny Serial Monitor), nevadi to -
    soubory se nahraji a jen se neoveri spusteni."""

    def __init__(self, board):
        self.repl = None
        self.note = ""
        self.buf = bytearray()
        self.lock = threading.Lock()
        self.stop = threading.Event()
        try:
            port = board.port_or_none()
        except CpyError:
            port = None
        if not port:
            self.note = "seriovy port desky nenalezen"
            return
        try:
            self.repl = Repl(port)
        except CpyError:
            self.note = f"port {port} je obsazeny (Serial Monitor / REPL / graf?)"
            return
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        while not self.stop.is_set():
            try:
                data = self.repl.ser.read(self.repl.ser.in_waiting or 1)
            except Exception:                   # noqa: BLE001 - port zmizel
                break
            if data:
                with self.lock:
                    self.buf += data

    def _data(self):
        """Prijata data bez terminalovych escape sekvenci."""
        with self.lock:
            data = bytes(self.buf)
        return _CSI_RE.sub(b"", _OSC_RE.sub(b"", data))

    def _wait(self, cond, timeout):
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            if cond(self._data()):
                return True
            time.sleep(0.1)
        return cond(self._data())

    def close(self):
        self.stop.set()
        if self.repl:
            self.thread.join(0.5)
            self.repl.close()

    def report(self, expect_code=True, timeout=8.0, collect=1.5):
        if not self.repl:
            say(f"Spusteni neoveruji: {self.note}. Vystup programu uvidis v Serial Monitoru.", "info")
            return
        if not self._wait(lambda d: b"soft reboot" in d or _START_RE.search(d), timeout):
            warn("Deska se po zapisu nerestartovala - neni vypnuty autoreload? Spust program: cpy reset")
            return
        if not expect_code:
            say("Deska se restartovala.", "done")
            return
        if not self._wait(lambda d: _START_RE.search(d), 3):
            warn(f"Deska se restartovala, ale nespustila zadny program (chybi {CP_ENTRY}?).")
            return
        self._wait(lambda d: b"Code done running" in d[_START_RE.search(d).end():], collect)
        data = self._data()
        m = _START_RE.search(data)
        text = data[m.end():].decode("utf-8", "replace")
        rows = [r.rstrip() for r in text.splitlines()
                if r.strip() and not r.strip().startswith(_STATUS_LINES)][:12]
        failed = "Traceback" in text
        if failed:
            warn(f"Deska spustila {m.group(1).decode()}, ale program skoncil chybou:")
        else:
            say(f"Deska spustila {m.group(1).decode()}." + (" Prvni vystup:" if rows else ""), "done")
        for r in rows:
            say("   " + r, "error" if failed else None)


@contextlib.contextmanager
def write_session(board, opts, expect_code=True):
    """Zapis na disk desky.

    Vychozi: JEN zapis na disk, seriovy port se vubec nepouziva. Prikazy pro
    praci se soubory (upload, main, save, wipe, setup) tak funguji i s
    otevrenym Serial Monitorem nebo REPL v jinem okne. Novy kod spusti
    CircuitPython sam (autoreload), jeho vystup uvidis v Serial Monitoru
    nebo v 'cpy monitor'.

    Port se pouzije jen na vyslovne prani:
      --watch  port se jen poslouchaji (nic se neposila) a overi se, ze se
               program po zapisu spustil; ukaze se jeho prvni vystup
      --stop   program se pred zapisem zastavi a pak jednou spusti
               (pro velka nahravani nebo kdyz je autoreload vypnuty)"""
    if opts.has("stop"):
        with board_paused(board):
            yield
        return
    if not opts.has("watch"):
        yield                                   # zaverecnou vetu pise kazdy prikaz sam
        return
    watcher = RestartWatcher(board)
    try:
        yield
        watcher.report(expect_code)
    finally:
        watcher.close()


@contextlib.contextmanager
def board_paused(board, reload_after=True):
    """Zastavi program na desce (deska ceka v REPL - zapis na disk ji v tu
    chvili nerestartuje). Na konci spusti code.py jednou znovu (Ctrl+D)."""
    repl = None
    port = board.port_or_none()
    if port:
        try:
            repl = Repl(port)
            repl.interrupt()
            say("Program na desce zastaven (deska ceka v REPL).", "info")
        except CpyError as e:
            if repl:
                repl.close()
            repl = None
            warn(str(e).splitlines()[0] + " - deska se muze behem kopirovani restartovat.")
    else:
        warn("Seriovy port desky nenalezen - deska se muze behem kopirovani nekolikrat restartovat.")
    try:
        yield repl
    finally:
        if repl:
            try:
                if reload_after:
                    time.sleep(0.5)             # at system dopise data na disk
                    repl.ser.reset_input_buffer()
                    repl.rx.clear()
                    if repl.soft_reload():
                        say("Deska znovu spustila code.py.", "done")
                    else:
                        warn("Restart programu se nepodarilo overit (cpy reset).")
            except Exception as e:              # noqa: BLE001 - port mohl zmizet
                warn(f"Restart programu selhal: {e}")
            repl.close()


def plan_upload(drive, rels, force=False):
    """Ktere soubory se opravdu musi kopirovat (lisi se od desky)
    a kolik mista na disku navic zaberou."""
    plan, needed = [], 0
    for rel in rels:
        src, dst = PROJECT / rel, drive / rel
        if not force and same_content(src, dst):
            continue
        old = dst.stat().st_size if dst.is_file() else 0
        needed += len(board_bytes(src)) - old
        plan.append(rel)
    return plan, needed


def check_space(drive, needed):
    free = shutil.disk_usage(drive).free
    if needed > free - 4096:
        raise CpyError(f"Na desce neni dost mista: potreba {needed} B, volno {free} B.")


def do_upload(drive, plan):
    """Zkopiruje soubory rychle za sebou (autoreload pak restartuje jen jednou)."""
    for rel in plan:
        say("Nahravam: " + col(rel, "dir" if "/" in rel else "file"))
        try:
            copy_file(PROJECT / rel, drive / rel)
        except OSError as e:
            raise CpyError(f"Kopirovani '{rel}' selhalo: {e}\n"
                           "       - neni disk jen pro cteni (boot.py se storage.remount)?")
    return len(plan)


def board_entries(drive):
    return sorted((e for e in drive.iterdir() if e.name not in SYSTEM_ENTRIES), key=lambda e: e.name.lower())


def do_wipe(drive):
    errors = 0
    for e in board_entries(drive):
        try:
            if e.is_dir():
                shutil.rmtree(e)
                say("Smazano: " + col(e.name + "/", "dir"))
            else:
                e.unlink()
                say("Smazano: " + col(e.name, "file"))
        except OSError as ex:
            say(col("ERROR", "error") + f": {e.name}: {ex}")
            errors += 1
    if errors:
        raise CpyError(f"Nepodarilo se smazat polozek: {errors}")


# --- Spolecne kroky podrobneho vypisu (Steps) pro CircuitPython ---
def cp_step_drive(st, board):
    """Krok 'Disk desky CIRCUITPY': najde disk a vypise o nem udaje."""
    st.head("Disk desky CIRCUITPY")
    drive = board.drive_or_none()
    if not drive:
        st.fail("disk CIRCUITPY nenalezen.",
                *(["deska je v rezimu bootloaderu (disk RPI-RP2) - stiskni RESET"]
                  if find_drives(BOOT_LABEL) else []),
                "je deska pripojena DATOVYM kabelem?",
                "je na desce CircuitPython (ne MicroPython)? Over: .\\cpy devices")
    boot = read_boot_out(drive)
    du = shutil.disk_usage(drive)
    st.info("disk:", f"{drive}  (volno {fmt_size(du.free)} z {fmt_size(du.total)})")
    st.info("firmware:", boot["line"] or "(boot_out.txt chybi)")
    return drive


def cp_step_port(st, board):
    """Krok 'Seriovy port desky': najde port a rekne, jak ho nasel."""
    st.head("Seriovy port desky")
    try:
        port = board.port_or_none()
    except CpyError as e:
        st.fail(str(e))
    if not port:
        st.fail("seriovy port desky s CircuitPythonem nenalezen.",
                "je deska pripojena? Over: .\\cpy devices",
                "port lze zadat rucne: --port COMx")
    uid = board.boot_info()["uid"]
    if board.opts.port:
        how = "zadan volbou --port / CIRCUITPY_PORT"
    elif uid and any(p.device == port for p in ports_for_uid(uid)):
        how = f"sparovan s diskem {board.drive_or_none()} podle UID {uid}"
    else:
        how = "podle USB VID:PID (disk CIRCUITPY nenalezen)"
    st.info("port:", port)
    st.info("nalezen:", how)
    return port


def open_repl_step(st, port):
    """Otevre seriovy port; kdyz nejde, ukonci krok srozumitelnou chybou."""
    try:
        return Repl(port)
    except CpyError as e:
        reason = str(e).splitlines()[0].split(": ", 1)[-1]
        st.fail(f"port {port} nelze otevrit.",
                f"duvod: {reason}",
                "neni otevreny Serial Monitor (odpoj ho: Stop Monitoring), REPL, graf "
                "nebo Thonny v jinem okne?")


def interrupt_step(st, repl):
    """Ctrl+C: zastavi program a dostane desku do REPL."""
    try:
        banner = repl.interrupt()
    except CpyError as e:
        st.fail(str(e), "odpoj a pripoj USB kabel a zkus to znovu")
    st.info("Ctrl+C:", "program zastaven, deska ceka v REPL")
    if b"safe mode" in banner.lower():
        st.info("pozor:", "deska je v NOUZOVEM REZIMU (safe mode) - viz .\\cpy check", "warn")
    return banner


def step_program_output(st, repl, seconds=2.5):
    """Krok 'Prvni vystup programu': par sekund cte, co program vypisuje
    (po restartu), a ukaze to. Vraci True, kdyz program skoncil chybou."""
    st.head(f"Prvni vystup programu ({seconds:g} s)")
    data = repl.read_for(seconds)
    text = _CSI_RE.sub(b"", _OSC_RE.sub(b"", data)).decode("utf-8", "replace")
    m = re.search(r"(\w+\.py) output:", text)       # CircuitPython ohlasi spusteny soubor
    if m:
        st.info("program:", m.group(1))
        text = text[m.end():]
    skip = _STATUS_LINES + ("MPY: soft reboot", "soft reboot")
    rows = [r.rstrip() for r in text.splitlines() if r.strip() and not r.strip().startswith(skip)]
    failed = "Traceback" in text
    if not rows:
        st.info("vystup:", "zatim nic (program nic nevypsal)")
    for r in rows[:15]:
        say("   | " + r, "error" if failed else None)
    if len(rows) > 15:
        st.info("", f"... a dalsich {len(rows) - 15} radku")
    return failed


def cp_upload_files(board, opts, rels, title, rules_info=True):
    """Spolecny postup pro 'cpy upload' a 'cpy main' s podrobnym vypisem."""
    st = Steps(title)

    # 1) Co se nahrava
    st.head("Co se nahrava")
    if rules_info:
        patterns = load_ignore()
        st.info("pravidla:", f".vscode/.ignoreCopy ({len(patterns)} masek)" if IGNORE_FILE.is_file()
                else ".vscode/.ignoreCopy NEEXISTUJE - plati jen vestavene pojistky")
        if (PROJECT / CP_ENTRY).is_file() and CP_ENTRY not in rels:
            st.info("pozor:", f"{CP_ENTRY} je v .ignoreCopy - nenahraje se", "warn")
    for rel in rels:
        if not (PROJECT / rel).is_file():
            st.fail(f"soubor '{rel}' v projektu neexistuje.")
        st.info("soubor:", f"{rel} ({(PROJECT / rel).stat().st_size} B)")
        if has_bom(PROJECT / rel):
            st.info("pozor:", f"{rel} ma BOM - na desku pujde bez nej", "warn")
    if not rels:
        st.done("Konec: v projektu neni nic k nahrani (vse vylucuje .ignoreCopy).")
        return

    # 2) Disk
    drive = cp_step_drive(st, board)

    # 3) Porovnani s deskou
    st.head("Porovnani s deskou")
    plan, needed = plan_upload(drive, rels, opts.has("all"))
    if opts.has("all"):
        st.info("volba --all:", "nahraji vsechno bez porovnani")
    st.info("zmenene:", f"{len(plan)}  " + ", ".join(plan) if plan else "0")
    st.info("beze zmeny:", len(rels) - len(plan))
    if not plan:
        st.done("Konec: na desce je vse aktualni, neni co nahravat. (Znovu spustit program: .\\cpy reset)")
        return
    free = shutil.disk_usage(drive).free
    if needed > free - 4096:
        st.fail(f"na desce neni dost mista (potreba {needed} B, volno {free} B).",
                "smaz z desky nepotrebne soubory: .\\cpy list, .\\cpy wipe")

    # 4) Nahravani
    st.head("Nahravani")
    if opts.has("stop"):
        st.info("zpusob:", "--stop: program se pres seriovy port zastavi a po zapisu jednou spusti")
    elif opts.has("watch"):
        st.info("zpusob:", "primo na disk, pak --watch: posloucham seriovy port")
    else:
        st.info("zpusob:", "primo na disk (seriovy port se nepouziva)")
    t0 = time.monotonic()
    with write_session(board, opts):
        for rel in plan:
            try:
                copy_file(PROJECT / rel, drive / rel, announce_bom=False)
            except OSError as e:
                st.fail(f"zapis '{rel}' na disk {drive} selhal: {e}",
                        "neni disk jen pro cteni (boot.py se storage.remount)?",
                        "nebyla deska behem zapisu odpojena?")
            st.info("nahrano:", f"{rel} ({(drive / rel).stat().st_size} B)")
    if (drive / "main.py").exists() and (drive / CP_ENTRY).exists():
        st.info("pozor:", "na desce je i main.py - CircuitPython ho ignoruje (spousti code.py)", "warn")
    st.done(f"Hotovo: nahrano {len(plan)} souboru za {time.monotonic() - t0:.1f} s. "
            "CircuitPython program sam restartuje (autoreload).")


def cp_upload(board, opts):
    """cpy upload: nahraje projekt (jen zmenene soubory) podle .ignoreCopy."""
    cp_upload_files(board, opts, project_files(), "Nahrani projektu na desku s CircuitPythonem")


def cp_main(board, opts):
    """cpy main: nahraje jen code.py."""
    cp_upload_files(board, opts, [CP_ENTRY], f"Nahrani {CP_ENTRY} na desku s CircuitPythonem",
                    rules_info=False)


def _fmt_mtime(path):
    with contextlib.suppress(OSError):
        return time.strftime("%d.%m.%Y %H:%M:%S", time.localtime(path.stat().st_mtime))
    return "?"


def cp_save(board, opts):
    """cpy save <soubor>: vola Run on Save po Ctrl+S. Zkopiruje JEDEN soubor,
    pokud ho .ignoreCopy nevylucuje a lisi se od desky. Seriovou linku
    nepouziva (studenti mivaji otevreny Serial Monitor).

    Vypis je zamerne podrobny a po krocich (jako puvodni copy.ps1), aby se
    v panelu Output -> Run On Save dalo poznat, kde presne je problem:
      1) ulozeny soubor   2) pravidla .ignoreCopy   3) disk CIRCUITPY
      4) cil na desce a porovnani obsahu   5) kopirovani
    Chyba se vzdy ohlasi jako 'ERROR: v kroku N - ...' s radou, co s ni delat."""
    if not opts.args:
        raise CpyError("Pouziti: cpy save <soubor>")
    raw = opts.args[0]
    st = Steps("Run on Save: kopirovani ulozeneho souboru na desku CIRCUITPY")

    # 1) Ulozeny soubor
    st.head("Ulozeny soubor")
    src = Path(raw) if Path(raw).is_absolute() else PROJECT / raw
    st.info("zadano:", raw)
    st.info("projekt:", PROJECT)
    try:
        rel = src.resolve().relative_to(PROJECT.resolve()).as_posix()
    except ValueError:
        st.info("vysledek:", "soubor neni soucasti projektu -> nekopiruji")
        st.done("Konec: soubor mimo projekt se na desku nekopiruje.")
        return 0
    st.info("v projektu:", rel)
    if not src.is_file():
        st.fail(f"soubor '{src}' neexistuje.", "byl mezitim prejmenovan nebo smazan?")
    st.info("velikost:", f"{src.stat().st_size} B, ulozen {_fmt_mtime(src)}")

    # 2) Pravidla .ignoreCopy
    st.head("Pravidla (co se na desku nekopiruje)")
    patterns = load_ignore()
    if IGNORE_FILE.is_file():
        st.info("soubor:", f"{IGNORE_FILE.relative_to(PROJECT).as_posix()} ({len(patterns)} masek)")
    else:
        st.info("soubor:", f"{IGNORE_FILE} NEEXISTUJE - plati jen vestavene pojistky")
    reason = skip_reason(rel, patterns)
    if reason:
        st.info("vysledek:", f"NEKOPIRUJE SE ({reason})")
        st.done(f"Konec: '{rel}' se na desku nekopiruje. Jestli tam patri, uprav .vscode/.ignoreCopy.")
        return 0
    st.info("vysledek:", "kopiruje se (zadna maska neodpovida)")

    # 3) Disk CIRCUITPY
    drive = cp_step_drive(st, board)
    free = shutil.disk_usage(drive).free

    # 4) Cil na desce a porovnani
    st.head("Cil na desce")
    dst = drive / rel
    st.info("cil:", dst)
    if dst.is_file():
        st.info("na desce:", f"{dst.stat().st_size} B, zmenen {_fmt_mtime(dst)}")
    else:
        st.info("na desce:", "zatim neni (novy soubor)")
    if has_bom(src):
        st.info("pozor:", "soubor je ulozeny jako 'UTF-8 with BOM' - na desku pujde bez BOM", "warn")
    if same_content(src, dst):
        st.info("porovnani:", "obsah je stejny -> nekopiruji (program se zbytecne nerestartuje)")
        st.done(f"Konec: '{rel}' je na desce aktualni.")
        return 0
    st.info("porovnani:", "obsah se lisi -> kopiruji")
    needed = len(board_bytes(src)) - (dst.stat().st_size if dst.is_file() else 0)
    if needed > free - 4096:
        st.fail(f"na desce neni dost mista (potreba {needed} B, volno {free} B).",
                "smaz z desky nepotrebne soubory: .\\cpy list, .\\cpy wipe")

    # 5) Kopirovani
    st.head("Kopirovani")
    t0 = time.monotonic()
    try:
        copy_file(src, dst, announce_bom=False)
    except OSError as e:
        st.fail(f"zapis na disk {drive} selhal: {e}",
                "neni disk jen pro cteni (boot.py se storage.remount)?",
                "nebyla deska behem zapisu odpojena?")
    st.info("vysledek:", f"OK, zapsano {dst.stat().st_size} B za {time.monotonic() - t0:.2f} s")
    st.done(f"Hotovo: {rel} -> {dst}. CircuitPython program sam restartuje (autoreload).")
    return 0


def cp_runmain(board, opts):
    """cpy runmain [soubor]: posle program do RAM desky a spusti ho (raw REPL).
    Na disk se nic nezapisuje. Moduly, ktere program importuje, se ale
    nacitaji Z DESKY - proto upozorni na zastarale soubory."""
    rel = opts.args[0] if opts.args else CP_ENTRY
    src = Path(rel) if Path(rel).is_absolute() else (Path.cwd() / rel)
    if not src.is_file():
        src = PROJECT / rel
    if not src.is_file():
        raise CpyError(f"Soubor '{rel}' nenalezen.")
    drive = board.drive_or_none()
    if drive:
        others = [r for r in project_files() if r.endswith((".py", ".mpy"))
                  and not (src.parent == PROJECT and r == src.name)]
        stale = plan_upload(drive, others)[0]
        if stale:
            warn("Importy se nacitaji z desky a tyto soubory tam maji starsi verzi: "
                 + ", ".join(stale) + " (nahraj je: cpy upload)")
    code = src.read_text(encoding="utf-8-sig")
    with Repl(board.port) as repl:
        repl.interrupt()
        say(f"Spoustim {src.name} z RAM (bez zapisu na disk). Preruseni: Ctrl+C", "info")
        line()
        repl.enter_raw()
        repl.raw_send(code)
        flt = OscFilter()
        err = b""
        try:
            _, err = repl.raw_collect(lambda d: write_raw(flt.feed(d)), timeout=None)
        except KeyboardInterrupt:
            repl.write(b"\x03")
            with contextlib.suppress(CpyError):
                _, err = repl.raw_collect(lambda d: write_raw(flt.feed(d)), timeout=5)
            say()
            say("Program prerusen (Ctrl+C).", "warn")
        repl.exit_raw()
        failed = err.strip() and b"KeyboardInterrupt" not in err
        if failed:
            say(err.decode("utf-8", "replace").rstrip(), "error")
        line()
        say("Deska ceka v REPL. Spustit code.py z disku: cpy reset", "info")
        if failed:
            raise CpyError(f"{src.name} skoncil chybou.")


def cp_repl(board, opts):
    """cpy repl: zastavi program a otevre interaktivni konzoli Pythonu."""
    if not stdin_is_console():
        raise CpyError("REPL potrebuje interaktivni terminal.")
    st = Steps("Konzole (REPL) desky s CircuitPythonem")
    port = cp_step_port(st, board)
    st.head("Zastaveni programu")
    with open_repl_step(st, port) as repl:
        banner = interrupt_step(st, repl)
        st.head("Konzole")
        st.info("konec:", "Ctrl+]  (program na desce pak stoji)")
        st.info("Ctrl+D:", "restart code.py")
        st.info("Ctrl+C:", "preruseni prikazu / programu")
        line()
        write_raw(OscFilter().feed(banner.rstrip(b"> ").rstrip() + b"\r\n>>> "))
        terminal(repl.ser)
        say()
    st.done("REPL ukoncen. Pokud program na desce stoji, spustis ho: tlacitko Restartovat program "
            "nebo .\\cpy reset")


def cp_monitor(board, opts):
    """cpy monitor: jen cte a vypisuje vystup desky (nic neposila)."""
    with Repl(board.port) as repl:
        say(f"Pouzivam port: {col(repl.port, 'info')}")
        if opts.has("restart"):
            repl.interrupt()
            repl.soft_reload()
            say("Program na desce spusten znovu.", "info")
        say("Sleduji vystup desky (nic neposilam). Konec: Ctrl+C", "info")
        line()
        flt = OscFilter()
        write_raw(flt.feed(repl._take()))
        try:
            while True:
                try:
                    data = repl.ser.read(repl.ser.in_waiting or 1)
                except Exception as e:          # noqa: BLE001
                    raise CpyError(f"Spojeni s deskou bylo preruseno: {e}")
                write_raw(flt.feed(data))
        except KeyboardInterrupt:
            say()
            line()
            say("Sledovani ukonceno.", "done")


def cp_list(board, opts):
    """cpy list: stromovy vypis disku CIRCUITPY (cte se primo z disku)."""
    drive = board.drive
    say(f"Disk desky: {col(drive, 'info')}")
    say("Obsah zarizeni:", "info")
    line()
    stats = print_tree(tree_from_disk(drive))
    du = shutil.disk_usage(drive)
    line()
    say(f"Souboru: {stats['files']}, velikost {fmt_size(stats['bytes'])}  |  "
        f"disk {fmt_size(du.total)}, volno {fmt_size(du.free)}")


CP_CHECK_SNIPPET = """
import sys, gc, supervisor, microcontroller
gc.collect()
print("verze   :", ".".join(str(v) for v in sys.implementation.version[:3]))
try:
    print("cpu     :", microcontroller.cpu.frequency // 1000000, "MHz, %.1f C" % microcontroller.cpu.temperature)
except Exception:
    pass
print("ram     :", gc.mem_free(), "B volno")
print("reload  :", "automaticky" if supervisor.runtime.autoreload else "VYPNUTY")
try:
    print("safe    :", supervisor.runtime.safe_mode_reason)
except AttributeError:
    pass
"""


def cp_check(board, opts):
    """cpy check: diagnostika - disk, firmware, port, test REPL."""
    problems = 0
    say("1) Disk CIRCUITPY", "info")
    drive = board.drive_or_none()
    if not drive:
        say(col("ERROR", "error") + ": Disk CIRCUITPY nenalezen.\n" + why_no_circuitpy())
        problems += 1
    else:
        du = shutil.disk_usage(drive)
        boot = read_boot_out(drive)
        say(f"   disk    : {drive}  ({fmt_size(du.total)}, volno {fmt_size(du.free)})")
        say(f"   firmware: {boot['line'] or '(boot_out.txt chybi)'}")
        if boot["board_id"]:
            say(f"   deska   : {boot['board_id']}   UID {boot['uid']}")
        if (drive / CP_ENTRY).is_file():
            say(f"   {CP_ENTRY:<8}: OK ({(drive / CP_ENTRY).stat().st_size} B)")
        elif (drive / "main.py").is_file():
            warn(f"Chybi {CP_ENTRY}, CircuitPython spusti main.py (MicroPython program?).")
        else:
            warn(f"Na desce chybi {CP_ENTRY} - deska nic nespusti (cpy main).")
        if (drive / CP_ENTRY).is_file() and (drive / "main.py").is_file():
            warn("Na desce je code.py i main.py - main.py se nespousti, lze ho smazat.")
        boot_py = drive / "boot.py"
        if boot_py.is_file():
            text = boot_py.read_text(encoding="utf-8", errors="replace")
            say("   boot.py : je na desce" + (" (meni pristup k disku - storage.remount!)"
                                             if "remount" in text or "disable_usb_drive" in text else ""))
        if du.free < 20 * 1024:
            warn("Na desce zbyva malo mista.")
    line()

    say("2) Seriovy port", "info")
    port = None
    try:
        port = board.port_or_none()
    except CpyError as e:
        say(col("ERROR", "error") + ": " + str(e))
        problems += 1
    for p in list_ports():
        if p.device == port:
            say(f"   {p.device}: deska s CircuitPythonem  (USB {vidpid(p)})", "done")
        elif is_micropython_port(p):
            say(f"   {p.device}: {known_name(p, MP_DEVICES) or 'MicroPython'} - neni CircuitPython, pouzij mpy")
    if not port and not opts.port:
        say(col("ERROR", "error") + ": Seriovy port desky nenalezen.")
        problems += 1
    if find_drives(BOOT_LABEL):
        warn("Je pripojena deska v rezimu bootloaderu (disk RPI-RP2).")
    line()

    if port and not opts.has("no-repl"):
        say("3) Test REPL (program na desce se zastavi a pak znovu spusti)", "info")
        try:
            with Repl(port) as repl:
                banner = repl.interrupt()
                if b"safe mode" in banner.lower():
                    warn("Deska je v NOUZOVEM REZIMU (safe mode) - viz cpy monitor / boot_out.txt.")
                    problems += 1
                out = repl.run_snippet(CP_CHECK_SNIPPET)
                for row in out.splitlines():
                    if row.strip():
                        say("   " + row.rstrip())
                say("   REPL OK", "done")
                if "VYPNUTY" in out:
                    warn("Autoreload je vypnuty - zapis na disk novy kod nespusti "
                         "(pouzij cpy upload --stop nebo cpy reset).")
                if repl.soft_reload():
                    say("   code.py znovu spusten.")
        except CpyError as e:
            say(col("ERROR", "error") + ": " + str(e))
            problems += 1
        line()

    if problems:
        raise CpyError(f"Diagnostika nasla problemy: {problems}")
    say("Diagnostika bez problemu.", "done")


def step_confirm(st, question, opts):
    """Krok 'Potvrzeni': --yes (napr. dialog v panelu) nebo otazka v terminalu."""
    st.head("Potvrzeni")
    if opts.has("yes"):
        st.info("potvrzeno:", "predem (volba --yes, napr. dialog v panelu VS Code)")
        return
    if not confirm(question, opts):
        st.done("Zruseno - nic se nesmazalo.", "warn")
        raise CpyError("Zruseno.")
    st.info("potvrzeno:", "v terminalu")


def cp_wipe(board, opts):
    """cpy wipe: smaze obsah disku (boot_out.txt zustane). --format preformatuje."""
    st = Steps("Smazani desky s CircuitPythonem" + (" (preformatovani)" if opts.has("format") else ""))
    drive = cp_step_drive(st, board)

    if opts.has("format"):
        step_confirm(st, f"Preformatovat disk {drive}? VSECHNA data na desce zmizi.", opts)
        st.head("Preformatovani (storage.erase_filesystem)")
        port = cp_step_port(st, board)
        with open_repl_step(st, port) as repl:
            interrupt_step(st, repl)
            repl.fire_and_forget("import storage\nstorage.erase_filesystem()\n")
        st.info("formatuji:", "deska se po naformatovani sama restartuje")
        board._drive = None
        time.sleep(2)
        drive = wait_for(lambda: board.drive_or_none(), 30)
        if not drive:
            st.fail("disk CIRCUITPY se po formatovani neobjevil.", "odpoj a pripoj USB kabel")
        st.info("disk:", f"{drive} znovu pripojen (obsahuje vychozi code.py)")
        st.done("Hotovo: disk desky je preformatovany.")
        return

    # 2) Obsah desky
    st.head("Obsah desky")
    entries = board_entries(drive)
    files = sum(1 for e in entries for f in ([e] if e.is_file() else e.rglob("*")) if f.is_file())
    st.info("polozek:", f"{len(entries)} v koreni, celkem {files} souboru")
    if entries:
        st.info("", ", ".join(e.name + ("/" if e.is_dir() else "") for e in entries[:10])
                + (", ..." if len(entries) > 10 else ""))
    if not entries:
        st.done("Konec: deska je uz prazdna, neni co mazat.")
        return

    # 3) Potvrzeni
    step_confirm(st, f"Smazat obsah disku {drive}? Operace je NEVRATNA.", opts)

    # 4) Mazani
    st.head("Mazani")
    errors = []
    with write_session(board, opts, expect_code=False):
        for e in entries:
            is_dir = e.is_dir()
            try:
                if is_dir:
                    shutil.rmtree(e)
                else:
                    e.unlink()
                st.info("smazano:", e.name + ("/" if is_dir else ""))
            except OSError as ex:
                errors.append(e.name)
                st.info("NELZE:", f"{e.name}: {ex}", "error")

    # 5) Kontrola
    st.head("Kontrola")
    left = board_entries(drive)
    if left:
        st.fail(f"na desce zustalo {len(left)} polozek: " + ", ".join(e.name for e in left[:10]),
                "nejsou soubory jen pro cteni nebo otevrene v jinem programu?",
                "uplne smazani: .\\cpy wipe --format")
    st.info("vysledek:", "deska je prazdna (boot_out.txt a systemove polozky zustavaji)")
    st.done("Hotovo: deska vymazana. Novy program nahrajes tlacitkem Nahrat projekt (.\\cpy upload).")


def cp_setup(board, opts):
    """cpy setup: smaze desku, nahraje cely projekt a vypise obsah."""
    drive = board.drive
    if not confirm(f"Smazat obsah {drive} a nahrat projekt?", opts):
        raise CpyError("Zruseno.")
    with write_session(board, opts):
        say("")
        say("KROK 1/3: mazani desky", "info")
        line()
        do_wipe(drive)
        say("")
        say("KROK 2/3: nahravani projektu", "info")
        line()
        plan, needed = plan_upload(drive, project_files(), True)
        check_space(drive, needed)
        do_upload(drive, plan)
    say("")
    say("KROK 3/3: obsah desky", "info")
    line()
    print_tree(tree_from_disk(drive))
    line("=")
    say("Deska je pripravena.", "done")


def cp_stop(board, opts):
    """cpy stop: zastavi program (Ctrl+C). S --wait nejdriv pocka, az se
    deska pripoji - tak jde zastavit i program, ktery desku hned po
    startu zahlti (nahrada puvodniho comStop.py)."""
    if opts.has("wait") and not board.port_or_none():
        say("Cekam na pripojeni desky... (preruseni: Ctrl+C)", "info")
        while not board.port_or_none():
            board._drive = None
            time.sleep(0.1)
    with Repl(board.port) as repl:
        banner = repl.interrupt()
    if b"safe mode" in banner.lower():
        warn("Deska je v nouzovem rezimu (safe mode).")
    say("Program zastaven, deska ceka v REPL. Znovu spustit: cpy reset", "done")


def cp_reset(board, opts):
    """cpy reset: znovu spusti code.py a ukaze jeho prvni vystup.
    --hard restartuje celou desku (jako tlacitko RESET)."""
    hard = opts.has("hard")
    st = Steps("Restart " + ("cele desky" if hard else "programu na desce") + " s CircuitPythonem")
    port = cp_step_port(st, board)
    drive = board.drive_or_none()
    if drive:
        st.info("code.py:", "na desce je" if (drive / CP_ENTRY).is_file()
                else "NA DESCE CHYBI - deska nema co spustit (nahraj projekt)",
                None if (drive / CP_ENTRY).is_file() else "warn")

    if hard:
        uid = board.boot_info()["uid"]
        st.head("Restart cele desky (microcontroller.reset)")
        with open_repl_step(st, port) as repl:
            interrupt_step(st, repl)
            repl.fire_and_forget("import microcontroller\nmicrocontroller.reset()\n")

        def back():
            return any(p.device == port or (uid and (p.serial_number or "").upper() == uid)
                       for p in list_ports())
        wait_for(lambda: not back(), 5, 0.1)    # port nejdriv zmizi ...
        st.info("port:", "odpojen, cekam na znovupripojeni")
        if not wait_for(back, 20):              # ... a pak se vrati
            st.fail("deska se po restartu neozvala.", "odpoj a pripoj USB kabel")
        st.info("port:", "znovu pripojen")
        st.done("Hotovo: deska restartovana, code.py se spousti. Vystup: Serial Monitor nebo .\\cpy monitor")
        return

    st.head("Restart programu")
    with open_repl_step(st, port) as repl:
        interrupt_step(st, repl)
        if not repl.soft_reload():
            st.fail("deska na Ctrl+D neodpovedela.", "zkus .\\cpy reset --hard nebo tlacitko RESET na desce")
        st.info("Ctrl+D:", "mekky restart - CircuitPython spousti code.py")
        failed = step_program_output(st, repl)
    if failed:
        st.done("Program skoncil chybou - viz vystup vyse (radek a typ chyby).", "warn")
    else:
        st.done("Hotovo: program bezi. Dalsi vystup: Serial Monitor nebo .\\cpy monitor")


def cp_plot(board, opts):
    """cpy plot: zivy graf hodnot ze seriove linky."""
    run_plotter(board.port, "Graf - CircuitPython", opts.number("seconds"))


def cp_lib(board, opts):
    """cpy lib ...: knihovny Adafruit pres nastroj circup (zapisuje na disk)."""
    chk = subprocess.run([TOOL_PY, "-m", "circup", "--version"], capture_output=True)
    if chk.returncode != 0:
        raise CpyError(f"Chybi nastroj circup: {pip_cmd('circup')}")
    drive = board.drive
    args = opts.args or ["freeze"]
    say("circup " + " ".join(args), "info")
    line()
    return subprocess.call([TOOL_PY, "-m", "circup", "--path", str(drive)] + args)


def cp_open(board, opts):
    """cpy open: otevre disk CIRCUITPY ve spravci souboru."""
    drive = board.drive
    if IS_WIN:
        os.startfile(str(drive))
    elif sys.platform == "darwin":
        subprocess.call(["open", str(drive)])
    else:
        subprocess.call(["xdg-open", str(drive)])
    say(f"Otevren disk {drive}", "done")


def to_bootloader(board):
    with Repl(board.port) as repl:
        repl.interrupt()
        say("Prepinam desku do bootloaderu...", "info")
        repl.fire_and_forget("import microcontroller\n"
                             "microcontroller.on_next_reset(microcontroller.RunMode.BOOTLOADER)\n"
                             "microcontroller.reset()\n")
    drive = wait_for(lambda: (find_drives(BOOT_LABEL) or [None])[0], 20)
    if not drive:
        raise CpyError("Disk RPI-RP2 se neobjevil. Drz tlacitko BOOTSEL a stiskni RESET.")
    say(f"Deska je v bootloaderu: disk {drive}", "done")
    return drive


def cp_bootloader(board, opts):
    """cpy bootloader: prepne desku do rezimu BOOTSEL (disk RPI-RP2)."""
    to_bootloader(board)
    say("Ven z bootloaderu: stiskni RESET, nebo nahraj firmware: cpy flash <soubor.uf2>", "info")


def cp_flash(board, opts):
    """cpy flash <soubor.uf2>: nahraje firmware (zkopiruje .uf2 na disk RPI-RP2)."""
    if not opts.args:
        raise CpyError("Zadej soubor s firmwarem: cpy flash <soubor.uf2>")
    uf2 = Path(opts.args[0])
    if not uf2.is_file() or uf2.suffix.lower() != ".uf2":
        raise CpyError(f"'{uf2}' neni soubor .uf2")
    boot = find_drives(BOOT_LABEL)
    if boot:
        target = boot[0]
    else:
        if not board.drive_or_none():
            raise CpyError("Deska neni v bootloaderu ani nema disk CIRCUITPY.\n"
                           "       Drz tlacitko BOOTSEL a stiskni RESET (objevi se disk RPI-RP2).")
        if not confirm(f"Prepnout desku do bootloaderu a nahrat {uf2.name}?", opts):
            raise CpyError("Zruseno.")
        target = to_bootloader(board)
    say(f"Nahravam {uf2.name} ({fmt_size(uf2.stat().st_size)}) na {target} ...", "info")
    with contextlib.suppress(OSError):          # deska se po zapisu sama odpoji
        shutil.copyfile(uf2, target / uf2.name)
    board._drive = None
    drive = wait_for(lambda: board.drive_or_none() if not find_drives(BOOT_LABEL) else None, 60)
    if drive:
        say(f"Firmware nahran: {read_boot_out(drive)['line']}", "done")
    elif not find_drives(BOOT_LABEL):
        say("Firmware nahran. Disk CIRCUITPY se neobjevil - mozna jde o jiny firmware (MicroPython?).", "done")
    else:
        raise CpyError("Deska zustala v bootloaderu - je soubor .uf2 urceny pro tuto desku?")


# ============================================================
# ODDIL 8  MicroPython - prikazy mpy
# ============================================================
# MicroPython deska nema USB disk. Vsechno jde pres seriovou linku
# nastrojem mpremote (python -m mpremote), ktery umi:
#   connect PORT   pripojit se k desce
#   cp A :B        kopirovat soubor na desku (':' = deska), cp -r = slozku
#   exec "kod"     spustit kratky kod na desce
#   run soubor.py  poslat soubor do RAM a spustit ho (bez zapisu na desku)
#   repl           interaktivni konzole
#   soft-reset / reset   mekky / tvrdy restart
# Vic prikazu jde spojit znakem '+' do jednoho spojeni (je to rychlejsi).
def mpremote_cmd(port, *args):
    return [TOOL_PY, "-m", "mpremote", "connect", port, *args]


def mpremote(port, *args, capture=False, timeout=None):
    """Spusti mpremote. capture=True: vystup se vrati misto vypsani."""
    try:
        if capture:
            return subprocess.run(mpremote_cmd(port, *args), capture_output=True, text=True,
                                  encoding="utf-8", errors="replace", timeout=timeout)
        return subprocess.run(mpremote_cmd(port, *args), timeout=timeout)
    except subprocess.TimeoutExpired:
        raise CpyError("Deska neodpovedela vcas (mpremote).")


def mp_require():
    import importlib.util
    if importlib.util.find_spec("mpremote") is None:
        raise missing_lib("mpremote")


def mp_locate(opts):
    """Najde MicroPython desku. Vraci (port, popis, rady) - port je None,
    kdyz deska neni; rady rikaji proc. Nic nevypisuje."""
    if opts.port:
        return opts.port, "zadana volbou --port / MICROPYTHON_PORT", []
    found = [p for p in list_ports() if is_micropython_port(p)]
    if not found:
        tips = []
        if find_drives(DRIVE_LABEL):
            tips.append("je pripojena deska s CircuitPythonem (disk CIRCUITPY) - na tu pouzij cpy")
        if find_drives(BOOT_LABEL):
            tips.append("deska je v rezimu bootloaderu (disk RPI-RP2) - stiskni RESET")
        tips.append("je deska pripojena DATOVYM kabelem a je na ni MicroPython? Over: .\\mpy devices")
        return None, "", tips
    p = found[0]
    desc = f"{known_name(p, MP_DEVICES) or p.description} (USB {vidpid(p)})"
    if len(found) > 1:
        desc += f"; pripojeno vic desek: {', '.join(q.device for q in found)} - jinou vyberes --port"
    return p.device, desc, []


def mp_find_port(opts):
    """Najde port MicroPython desky (strucny vypis)."""
    port, desc, tips = mp_locate(opts)
    if not port:
        raise CpyError("MicroPython deska nenalezena.\n" + "\n".join("       - " + t for t in tips))
    say(f"Deska: {desc} na {col(port, 'info')}")
    return port


def mp_responds(port):
    return mpremote(port, "exec", "pass", capture=True, timeout=20).returncode == 0


MP_BUSY_TIPS = ("neni otevreny REPL v jinem okne?",
                "neni spusteny Thonny / Mu / jiny editor?",
                "neni port obsazeny jinym programem (Serial Monitor, graf)?")


def mp_ready_port(opts, st=None):
    """Najde desku a overi, ze odpovida. Kdyz ne, zkusi ji restartovat.
    (Stejny postup jako puvodni Get-ReadyPort v utils.ps1.)
    S parametrem st (Steps) vypisuje vse jako krok 'Deska s MicroPythonem'."""
    mp_require()
    if st is None:
        port = mp_find_port(opts)
        if mp_responds(port):
            return port
        say("Deska neodpovida, zkousim restart...", "info")
        mpremote(port, "reset", capture=True, timeout=20)
        time.sleep(1.5)
        if mp_responds(port):
            return port
        raise CpyError("Zarizeni nereaguje ani po restartu.\n"
                       + "\n".join("       - " + t for t in MP_BUSY_TIPS))

    st.head("Deska s MicroPythonem")
    port, desc, tips = mp_locate(opts)
    if not port:
        st.fail("MicroPython deska nenalezena.", *tips)
    st.info("port:", port)
    st.info("deska:", desc)
    t0 = time.monotonic()
    r = mpremote(port, "exec", "pass", capture=True, timeout=20)
    if r.returncode == 0:
        st.info("odpoved:", f"OK ({time.monotonic() - t0:.1f} s)")
        return port
    err = (r.stderr or "") + (r.stdout or "")
    if "in use" in err or "failed to access" in err:    # port drzi jiny program
        st.fail(f"port {port} je obsazeny jinym programem.", *MP_BUSY_TIPS)
    st.info("odpoved:", "zadna - zkousim restart desky", "warn")
    mpremote(port, "reset", capture=True, timeout=20)
    time.sleep(1.5)
    if mp_responds(port):
        st.info("po restartu:", "OK")
        return port
    st.fail("deska neodpovida ani po restartu.", *MP_BUSY_TIPS)


def mp_upload_items():
    """Polozky z .vscode/upload_config.txt (soubory a slozky k nahrani)."""
    if not UPLOAD_CONFIG.is_file():
        raise CpyError(f"Nenalezen soubor s konfiguraci: {UPLOAD_CONFIG}")
    items = []
    for raw in UPLOAD_CONFIG.read_text(encoding="utf-8-sig").splitlines():
        s = raw.strip()
        if s and not s.startswith("#"):
            items.append(s.replace("\\", "/").rstrip("/"))
    return items


def mp_copy(port, items):
    """Nahraje soubory a slozky jednim spojenim mpremote (prikazy spojene '+')."""
    args = []
    for item in items:
        src = PROJECT / item
        if not src.exists():
            say(col("ERROR", "error") + f": Preskakuji (nenalezeno): {item}")
            continue
        # mpremote kopiruje soubory beze zmeny, BOM tedy jen ohlasime
        for f in ([src] if src.is_file() else sorted(src.rglob("*.py"))):
            if has_bom(f):
                warn(f"{f.relative_to(PROJECT).as_posix()} je ulozeny jako 'UTF-8 with BOM' - "
                     f"na desce skonci chybou NameError ({BOM_HELP}).")
        if args:
            args.append("+")
        if src.is_dir():
            say("Nahravam slozku: " + col(item, "dir"))
            args += ["cp", "-r", item, ":"]
        else:
            say("Nahravam soubor: " + col(item, "file"))
            args += ["cp", item, ":"]
    if not args:
        raise CpyError("Neni co nahrat.")
    line()
    r = subprocess.run(mpremote_cmd(port, *args), cwd=str(PROJECT))
    if r.returncode != 0:
        raise CpyError("Nahravani selhalo.")


def mp_upload_files(opts, items, title, source):
    """Spolecny postup pro 'mpy upload' a 'mpy main' s podrobnym vypisem."""
    st = Steps(title)

    # 1) Co se nahrava
    st.head("Co se nahrava")
    st.info("seznam:", source)
    existing, total_files = [], 0
    for item in items:
        src = PROJECT / item
        if not src.exists():
            st.info("CHYBI:", f"{item} - v projektu neexistuje, preskakuji", "error")
            continue
        if src.is_dir():
            files = [f for f in src.rglob("*") if f.is_file()]
            st.info("slozka:", f"{item}/ ({len(files)} souboru, {fmt_size(sum(f.stat().st_size for f in files))})")
        else:
            files = [src]
            st.info("soubor:", f"{item} ({src.stat().st_size} B)")
        for f in files:
            if has_bom(f):
                st.info("pozor:", f"{f.relative_to(PROJECT).as_posix()} ma BOM - na desce skonci chybou "
                        f"NameError ({BOM_HELP})", "warn")
        existing.append(item)
        total_files += len(files)
    if not existing:
        st.fail("neni co nahrat - zadna polozka neexistuje.", f"zkontroluj {source}")

    # 2) Deska
    port = mp_ready_port(opts, st)

    # 3) Nahravani pres mpremote (vsechno jednim spojenim, prikazy spojene '+')
    st.head("Nahravani (mpremote)")
    args = []
    for item in existing:
        if args:
            args.append("+")
        args += ["cp", "-r", item, ":"] if (PROJECT / item).is_dir() else ["cp", item, ":"]
    st.info("prikaz:", "mpremote connect " + port + " " + " ".join(args))
    t0 = time.monotonic()
    up_to_date, last = 0, []
    proc = subprocess.Popen(mpremote_cmd(port, *args), cwd=str(PROJECT), stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
    for row in proc.stdout:                     # prubezne, at je videt kazdy soubor
        row = row.rstrip()
        if not row:
            continue
        last = (last + [row])[-4:]
        if row.startswith("Up to date:"):
            up_to_date += 1
            st.info("beze zmeny:", row[len("Up to date:"):].strip().lstrip("./"))
        elif row.startswith("cp "):
            st.info("mpremote:", row)
        else:
            say("   | " + row)
    rc = proc.wait()
    if rc != 0:
        st.fail(f"mpremote skoncil chybou (kod {rc}).", *last, *MP_BUSY_TIPS)
    copied = max(0, total_files - up_to_date)
    st.info("vysledek:", f"OK za {time.monotonic() - t0:.1f} s - nahrano {copied}, beze zmeny {up_to_date}")
    st.done("Hotovo. MicroPython program po nahrani SAM NESPUSTI - spust ho tlacitkem "
            "'Spustit main.py' nebo .\\mpy reset.")


def mp_upload(opts):
    """mpy upload: nahraje polozky z upload_config.txt."""
    mp_upload_files(opts, mp_upload_items(), "Nahrani projektu na desku s MicroPythonem",
                    UPLOAD_CONFIG.relative_to(PROJECT).as_posix())


def mp_main(opts):
    """mpy main: nahraje jen main.py."""
    mp_upload_files(opts, [MP_ENTRY], f"Nahrani {MP_ENTRY} na desku s MicroPythonem",
                    f"jen {MP_ENTRY} (prikaz mpy main)")


def mp_runmain(opts):
    """mpy runmain [soubor]: spusti main.py (nebo jiny soubor) z RAM bez zapisu."""
    rel = opts.args[0] if opts.args else MP_ENTRY
    src = Path(rel) if Path(rel).is_absolute() else (Path.cwd() / rel)
    if not src.is_file():
        src = PROJECT / rel
    if not src.is_file():
        raise CpyError(f"Soubor '{rel}' nenalezen.")
    port = mp_ready_port(opts)
    say(f"Spoustim {src.name} z RAM (bez zapisu na desku). Preruseni: Ctrl+C", "info")
    line()
    run_file = src
    if has_bom(src):                            # mpremote by poslal i BOM -> NameError
        import tempfile
        tmp = tempfile.NamedTemporaryFile("wb", suffix=".py", delete=False)
        tmp.write(board_bytes(src))
        tmp.close()
        run_file = Path(tmp.name)
    try:
        with ctrl_c_to_child():
            r = subprocess.run(mpremote_cmd(port, "run", str(run_file)))
    finally:
        if run_file != src:
            run_file.unlink()
    line()
    if r.returncode != 0:
        raise CpyError(f"{src.name} skoncil chybou.")
    say(f"{src.name} dokoncen.", "done")


def mp_repl(opts):
    """mpy repl: interaktivni konzole (konec Ctrl+])."""
    st = Steps("Konzole (REPL) desky s MicroPythonem")
    port = mp_ready_port(opts, st)
    st.head("Konzole (mpremote repl)")
    st.info("konec:", "Ctrl+]")
    st.info("Ctrl+C:", "preruseni prikazu / programu")
    st.info("Ctrl+D:", "restart - spusti main.py")
    line()
    with ctrl_c_to_child():
        r = subprocess.run(mpremote_cmd(port, "repl"))
    if r.returncode != 0:
        st.fail(f"REPL skoncil chybou (kod {r.returncode}).", *MP_BUSY_TIPS)
    st.done("REPL ukoncen.")


# Kod, ktery se spusti NA DESCE: projde soubory a vypise je jako JSON.
# (mode & 0x4000 znamena "slozka", st[6] je velikost souboru)
MP_WALK_CODE = """
import os, json
def walk(p):
    res = []
    try:
        items = os.listdir(p)
    except:
        return res
    dirs, files = [], []
    for n in items:
        full = p + '/' + n if p != '/' else '/' + n
        try:
            st = os.stat(full)
        except:
            continue
        if st[0] & 0x4000:
            dirs.append(n)
        else:
            files.append((n, st[6]))
    res.append((p, dirs, files))
    for d in dirs:
        res.extend(walk(p + '/' + d if p != '/' else '/' + d))
    return res
print(json.dumps(walk('/')))
"""


def mp_tree(port):
    """Nacte z desky seznam souboru a postavi z nej strom pro print_tree."""
    r = mpremote(port, "exec", MP_WALK_CODE, capture=True, timeout=30)
    out = r.stdout or ""
    start, end = out.find("["), out.rfind("]")
    if r.returncode != 0 or start < 0 or end <= start:
        raise CpyError("Vypis souboru z desky se nepodaril.\n" + (r.stderr or out).strip())
    data = json.loads(out[start:end + 1])
    nodes = {path: {"files": sorted((f[0], f[1]) for f in files), "dirs": [], "error": None}
             for path, _dirs, files in data}
    for path, dirs, _files in data:
        for d in sorted(dirs):
            child = (path.rstrip("/") + "/" + d) if path != "/" else "/" + d
            if child in nodes:
                nodes[path]["dirs"].append((d, nodes[child]))
    return nodes.get("/", {"files": [], "dirs": [], "error": None})


def mp_list(opts):
    """mpy list: stromovy vypis souboru na desce s velikostmi."""
    port = mp_ready_port(opts)
    say("Obsah zarizeni:", "info")
    line()
    stats = print_tree(mp_tree(port))
    line()
    say(f"Souboru: {stats['files']}, velikost {fmt_size(stats['bytes'])}")


# Kod pro desku: rekurzivne smaze vsechny soubory a slozky.
MP_WIPE_CODE = """
import os
def wipe(path=''):
    for name in os.listdir(path if path else '/'):
        full = name if path == '' else path + '/' + name
        try:
            if os.stat(full)[0] & 0x4000:
                wipe(full)
                os.rmdir(full)
            else:
                os.remove(full)
            print('Smazano:', full)
        except Exception as e:
            print('ERR:', full, e)
wipe()
"""


def mp_do_wipe(port, st=None):
    """Smaze vsechno na desce (kod MP_WIPE_CODE bezi primo na desce).
    S parametrem st (Steps) vypisuje smazane polozky jako udaje kroku."""
    r = mpremote(port, "exec", MP_WIPE_CODE, capture=True, timeout=60)
    out = (r.stdout or "").strip()
    errors = 0
    for row in out.splitlines():
        row = row.strip()
        if row.startswith("ERR:"):
            errors += 1
            if st:
                st.info("NELZE:", row[4:].strip(), "error")
            else:
                say(col("ERROR", "error") + ": " + row[4:].strip())
        elif row.startswith("Smazano:"):
            name = row[8:].strip()
            if st:
                st.info("smazano:", name)
            else:
                say("Smazano: " + col(name, "file"))
    if r.returncode != 0:
        detail = (r.stderr or "").strip()
        if st:
            st.fail("mazani na desce selhalo.", *(detail.splitlines()[-2:] if detail else []), *MP_BUSY_TIPS)
        raise CpyError("Mazani selhalo.\n" + detail)
    if errors and not st:
        raise CpyError(f"Nepodarilo se smazat polozek: {errors}")
    return errors


def mp_count_files(node):
    """Pocet souboru a celkova velikost ve stromu z mp_tree()."""
    files = sum(1 for _ in node["files"]) + sum(mp_count_files(d)[0] for _, d in node["dirs"])
    size = sum(s for _, s in node["files"]) + sum(mp_count_files(d)[1] for _, d in node["dirs"])
    return files, size


def mp_wipe(opts):
    """mpy wipe: smaze vsechny soubory na desce (s potvrzenim)."""
    st = Steps("Smazani desky s MicroPythonem")
    port = mp_ready_port(opts, st)

    # 2) Obsah desky
    st.head("Obsah desky")
    try:
        tree = mp_tree(port)
    except CpyError as e:
        st.fail("obsah desky se nepodarilo nacist.", str(e).splitlines()[0], *MP_BUSY_TIPS)
    files, size = mp_count_files(tree)
    names = [n for n, _ in tree["files"]] + [n + "/" for n, _ in tree["dirs"]]
    st.info("souboru:", f"{files} ({fmt_size(size)})")
    if names:
        st.info("v koreni:", ", ".join(names[:10]) + (", ..." if len(names) > 10 else ""))
    if not names:
        st.done("Konec: deska je uz prazdna, neni co mazat.")
        return

    # 3) Potvrzeni
    step_confirm(st, "Smazat VSECHNY soubory na desce? Operace je NEVRATNA.", opts)

    # 4) Mazani
    st.head("Mazani")
    errors = mp_do_wipe(port, st)

    # 5) Kontrola
    st.head("Kontrola")
    left, _ = mp_count_files(mp_tree(port))
    if left or errors:
        st.fail(f"na desce zustalo {left} souboru (chyb pri mazani: {errors}).",
                "neni nektery soubor prave pouzivany? Zkus .\\mpy reset a smazat znovu")
    st.info("vysledek:", "deska je prazdna")
    st.done("Hotovo: deska vymazana. Novy program nahrajes tlacitkem Nahrat projekt (.\\mpy upload).")


def mp_setup(opts):
    """mpy setup: wipe + upload + list."""
    port = mp_ready_port(opts)
    if not confirm("Smazat desku a nahrat projekt?", opts):
        raise CpyError("Zruseno.")
    say("")
    say("KROK 1/3: mazani desky", "info")
    line()
    mp_do_wipe(port)
    say("")
    say("KROK 2/3: nahravani projektu", "info")
    line()
    mp_copy(port, mp_upload_items())
    say("")
    say("KROK 3/3: obsah desky", "info")
    line()
    print_tree(mp_tree(port))
    line("=")
    say("Deska je pripravena. Spustit program: mpy reset", "done")


MP_INFO_CODE = """
import os, gc
u = os.uname()
print("firmware:", u.version)
print("deska   :", u.machine)
try:
    s = os.statvfs("/")
    print("disk    :", s[0] * s[2], "B, volno", s[0] * s[3], "B")
except Exception:
    pass
gc.collect()
print("ram     :", gc.mem_free(), "B volno")
"""


def mp_check(opts):
    """mpy check: diagnostika - port, odpoved REPL, informace, soubory."""
    say("1) Port a odpoved desky", "info")
    port = mp_ready_port(opts)
    say("   REPL OK", "done")
    line()
    say("2) Informace o desce", "info")
    r = mpremote(port, "exec", MP_INFO_CODE, capture=True, timeout=20)
    for row in (r.stdout or "").splitlines():
        if row.strip():
            say("   " + row.rstrip())
    if r.returncode != 0:
        warn("Informace se nepodarilo nacist: " + (r.stderr or "").strip())
    line()
    say("3) Obsah zarizeni", "info")
    print_tree(mp_tree(port))
    line()
    say("Diagnostika dokoncena.", "done")


def mp_reset(opts):
    """mpy reset: mekky restart, po kterem deska spusti main.py.
    --hard = restart cele desky (machine.reset), jako stisk tlacitka RESET.

    Pozor na past: 'mpremote soft-reset' restartuje desku z raw REPL a
    MicroPython v tom rezimu main.py NESPUSTI. Proto se mekky restart
    posila z normalniho REPL (Ctrl+C, Ctrl+B, Ctrl+D) - stejne jako u cpy."""
    hard = opts.has("hard")
    st = Steps("Spusteni main.py na desce s MicroPythonem" + (" (restart cele desky)" if hard else ""))
    port = mp_ready_port(opts, st)

    if hard:
        st.head("Restart cele desky (machine.reset)")
        r = mpremote(port, "reset", capture=True, timeout=20)
        if r.returncode != 0:
            st.fail("restart selhal.", *((r.stderr or "").strip().splitlines()[-2:]), *MP_BUSY_TIPS)
        st.info("vysledek:", "deska se restartuje jako po stisku tlacitka RESET")
        st.done("Hotovo: main.py se spousti. Vystup programu uvidis v Konzoli (REPL): .\\mpy repl")
        return

    st.head("Restart programu")
    with open_repl_step(st, port) as repl:
        interrupt_step(st, repl)
        try:
            has_main = repl.run_snippet("import os\nprint('main.py' in os.listdir('/'))").strip()
        except CpyError:
            has_main = "?"
        if has_main == "False":
            st.fail(f"na desce neni {MP_ENTRY} - neni co spustit.",
                    "nahraj ho tlacitkem Nahrat projekt (.\\mpy upload)")
        st.info(f"{MP_ENTRY}:", "na desce je" if has_main == "True" else "nepodarilo se overit")
        if not repl.soft_reload():
            st.fail("deska na Ctrl+D neodpovedela.", "zkus .\\mpy reset --hard nebo tlacitko RESET na desce")
        st.info("Ctrl+D:", f"mekky restart - MicroPython spousti {MP_ENTRY}")
        failed = step_program_output(st, repl)
    if failed:
        st.done("Program skoncil chybou - viz vystup vyse (radek a typ chyby).", "warn")
    else:
        st.done("Hotovo: main.py bezi. Dalsi vystup uvidis v Konzoli (REPL): .\\mpy repl")


def mp_plot(opts):
    """mpy plot: zivy graf hodnot ze seriove linky."""
    mp_require()
    run_plotter(mp_find_port(opts), "Graf - MicroPython", opts.number("seconds"))


# ============================================================
# ODDIL 9  Napoveda, cteni parametru a hlavni funkce
# ============================================================
HELP_MAIN = """Pouziti:  python .vscode/deska.py <nastroj> <prikaz> [volby]

  mpy <prikaz>    MicroPython (micro:bit, Raspberry Pi Pico, Pico:ed v2)
  cpy <prikaz>    CircuitPython (Pico:ed v1 a v2, disk CIRCUITPY)
  devices         jake desky jsou pripojene a ktery nastroj na ne pouzit
  vscode          nastavi panel a Run on Save v .vscode/settings.json

Kratce:  .\\mpy help   .\\cpy help   (Windows PowerShell)
         ./mpy.sh help ./cpy.sh help (Linux / macOS)
"""

HELP_MPY = """Pouziti: mpy <prikaz> [volby]          (v PowerShellu: .\\mpy <prikaz>)

  upload                nahraje soubory a slozky z .vscode/upload_config.txt
  main                  nahraje jen main.py
  runmain [soubor]      spusti main.py (nebo jiny soubor) z RAM bez zapisu na desku
  repl                  interaktivni konzole Pythonu na desce   (konec: Ctrl+])
  list                  stromovy vypis souboru na desce
  check                 diagnostika desky
  wipe                  smaze vsechny soubory na desce (s potvrzenim)
  setup                 kompletni priprava: wipe + upload + list
  reset [--hard]        restart: spusti main.py (--hard = restart cele desky)
  plot                  zivy graf hodnot, ktere program vypisuje pres print()
  devices               jake desky jsou pripojene
  help                  tato napoveda

Volby:
  --port COMx           port desky (jinak automaticky; promenna MICROPYTHON_PORT)
  -y, --yes             bez potvrzovaci otazky (wipe, setup)
"""

HELP_CPY = """Pouziti: cpy <prikaz> [volby]          (v PowerShellu: .\\cpy <prikaz>)

Stejne prikazy jako mpy:
  upload [--all]        nahraje projekt na disk CIRCUITPY (jen zmenene soubory, --all = vse);
                        co se nahrava, urcuje .vscode/.ignoreCopy
  main [--all]          nahraje jen code.py   (alias: code)
  runmain [soubor]      spusti code.py (nebo jiny soubor) z RAM bez zapisu na disk
  repl                  interaktivni konzole Pythonu na desce   (konec: Ctrl+])
  list                  stromovy vypis obsahu desky
  check [--no-repl]     diagnostika desky
  wipe [--format]       smaze obsah desky (--format = preformatovani disku)
  setup                 kompletni priprava: wipe + upload + list
  reset [--hard]        znovu spusti code.py (--hard = restart cele desky)
  plot                  zivy graf hodnot, ktere program vypisuje pres print()
  devices               jake desky jsou pripojene
  help                  tato napoveda

Jen pro CircuitPython:
  save <soubor>         zkopiruje jeden soubor (pouziva Run on Save po Ctrl+S)
  stop [--wait]         zastavi program (Ctrl+C); --wait nejdriv pocka na pripojeni desky
  monitor [--restart]   sleduje vystupy print() bez zasahu do desky (konec: Ctrl+C)
  lib [prikaz]          knihovny pres circup: install X, uninstall X, update, list, freeze
  open                  otevre disk CIRCUITPY ve spravci souboru
  bootloader            prepne desku do rezimu BOOTSEL (disk RPI-RP2)
  flash <soubor.uf2>    nahraje firmware do desky

Volby:
  --port COMx           seriovy port desky (jinak automaticky; promenna CIRCUITPY_PORT)
  --drive F:            disk desky (jinak automaticky; promenna CIRCUITPY_PATH)
  -y, --yes             bez potvrzovaci otazky (wipe, setup, flash)
  --watch               (upload, main, wipe, setup) po zapisu poslouchaji seriovy port
                        a overi, ze se program spustil (ukaze jeho prvni vystup)
  --stop                (upload, main, wipe, setup) pred zapisem zastavi program pres
                        seriovy port a pak ho jednou spusti

Prace se soubory (save, upload, main, list, wipe, setup) seriovy port NEPOUZIVA -
soubory se zapisuji primo na disk (jako pri Ctrl+S) a novy kod spusti autoreload.
Funguje to i s otevrenym Serial Monitorem. Port potrebuji jen prikazy, ktere
s deskou mluvi: repl, runmain, monitor, plot, stop, reset, check, wipe --format,
bootloader - pred nimi Serial Monitor odpoj.
"""

# Tabulky prikazu: jmeno -> (funkce, povolene volby).
# Funkce CircuitPythonu dostavaji (board, opts), MicroPythonu jen (opts).
CPY_COMMANDS = {
    "upload": (cp_upload, {"all", "stop", "watch"}),
    "main": (cp_main, {"all", "stop", "watch"}),
    "code": (cp_main, {"all", "stop", "watch"}),
    "save": (cp_save, set()),
    "runmain": (cp_runmain, set()),
    "run": (cp_runmain, set()),
    "repl": (cp_repl, set()),
    "list": (cp_list, set()),
    "ls": (cp_list, set()),
    "check": (cp_check, {"no-repl"}),
    "wipe": (cp_wipe, {"format", "stop", "watch"}),
    "setup": (cp_setup, {"stop", "watch"}),
    "stop": (cp_stop, {"wait"}),
    "reset": (cp_reset, {"hard"}),
    "monitor": (cp_monitor, {"restart"}),
    "plot": (cp_plot, {"seconds"}),
    "lib": (cp_lib, set()),
    "open": (cp_open, set()),
    "bootloader": (cp_bootloader, set()),
    "flash": (cp_flash, set()),
}
MPY_COMMANDS = {
    "upload": (mp_upload, set()),
    "main": (mp_main, set()),
    "runmain": (mp_runmain, set()),
    "run": (mp_runmain, set()),
    "repl": (mp_repl, set()),
    "list": (mp_list, set()),
    "ls": (mp_list, set()),
    "check": (mp_check, set()),
    "wipe": (mp_wipe, set()),
    "setup": (mp_setup, set()),
    "reset": (mp_reset, {"hard"}),
    "plot": (mp_plot, {"seconds"}),
}
VALUE_OPTIONS = {"--port": "port", "-p": "port", "--drive": "drive", "-d": "drive"}


class Options:
    """Co uzivatel napsal na prikazovou radku."""

    def __init__(self, tool):
        env_port = "CIRCUITPY_PORT" if tool == "cpy" else "MICROPYTHON_PORT"
        self.port = os.environ.get(env_port) or None
        self.drive = os.environ.get("CIRCUITPY_PATH") or None
        self.flags = {}                 # volby typu --all (hodnota True) nebo --seconds=5
        self.args = []                  # ostatni slova za prikazem
        self.cmd = None

    def has(self, flag):
        return flag in self.flags

    def number(self, flag):
        v = self.flags.get(flag)
        try:
            return float(v) if v not in (None, True) else None
        except ValueError:
            raise CpyError(f"Volba --{flag} potrebuje cislo.")


def parse_args(tool, argv):
    o = Options(tool)
    i = 0
    while i < len(argv):
        a = argv[i]
        if o.cmd == "lib" and a not in VALUE_OPTIONS and not a.startswith(("--port=", "--drive=")):
            o.args.append(a)                    # vse za "cpy lib" patri nastroji circup
        elif a in VALUE_OPTIONS:
            if i + 1 >= len(argv):
                raise CpyError(f"Volba {a} potrebuje hodnotu.")
            setattr(o, VALUE_OPTIONS[a], argv[i + 1])
            i += 1
        elif a.startswith(("--port=", "--drive=")):
            key, val = a[2:].split("=", 1)
            setattr(o, key, val)
        elif a in ("-y", "--yes"):
            o.flags["yes"] = True
        elif a in ("-h", "--help", "/?"):
            o.flags["help"] = True
        elif a.startswith("--"):
            key, _, val = a[2:].partition("=")
            o.flags[key] = val if val else True
        elif o.cmd is None:
            o.cmd = a.lower()
        else:
            o.args.append(a)
        i += 1
    return o


def main(argv):
    tool = argv[0].lower() if argv else ""
    if "--json" not in argv:                    # JSON cte program - bez hlavicky
        print(f"{SCRIPT_NAME} {tool} - verze: {SCRIPT_VERSION} ({SCRIPT_DATE})".replace("  ", " "))
        line()
    try:
        if tool in ("devices", "vscode"):
            fn = cmd_devices if tool == "devices" else cmd_vscode
            return fn(parse_args("cpy", argv[1:])) or 0
        if tool not in ("mpy", "cpy"):
            print(HELP_MAIN)
            return 0 if tool in ("", "help", "-h", "--help") else 1
        opts = parse_args(tool, argv[1:])
        commands, helptext = (CPY_COMMANDS, HELP_CPY) if tool == "cpy" else (MPY_COMMANDS, HELP_MPY)
        if opts.cmd in (None, "help") or opts.has("help"):
            print(helptext)
            return 0
        if opts.cmd == "devices":
            cmd_devices(opts)
            return 0
        if opts.cmd not in commands:
            say(col("ERROR", "error") + f": Neznamy prikaz: {opts.cmd}")
            print(helptext)
            return 1
        fn, allowed = commands[opts.cmd]
        unknown = set(opts.flags) - allowed - {"yes"}
        if unknown:
            raise CpyError(f"Neznama volba pro '{opts.cmd}': " + ", ".join("--" + f for f in sorted(unknown)))
        rc = fn(Board(opts), opts) if tool == "cpy" else fn(opts)
        return rc if isinstance(rc, int) else 0
    except CpyError as e:
        say(col("ERROR", "error") + ": " + str(e))
        return 1
    except KeyboardInterrupt:
        say()
        say("Preruseno.", "warn")
        return 130


if __name__ == "__main__":
    use_venv()
    sys.exit(main(sys.argv[1:]))
