r"""Testy prikazu CLI (.vscode/deska.py: cpy, mpy, devices, vscode).

Pro spravce sablony - studenti je nepotrebuji (proto jsou v .vscode/, kam
studenti nechodi a co se nikdy nenahrava na desku). Spusteni z korene projektu:

    .venv\Scripts\python .vscode\tests\test_deska.py            bez desky
    .venv\Scripts\python .vscode\tests\test_deska.py --hw       + pripojene desky
    .venv\Scripts\python .vscode\tests\test_deska.py --hw --all-boards
    .venv\Scripts\python .vscode\tests\test_deska.py --hw --only microbit

Testy si v docasne slozce vytvori zkusebni projekt (deska.py a upload.toml
z teto sablony + vygenerovane programy a knihovny). Programy jen vypisuji
znacky pres print() - nepotrebuji zadny hardware krome samotne desky.

--hw: na kazde testovane desce se NEJDRIV ZALOHUJE cely obsah, pak se
projdou prikazy (vcetne zapisu, wipe a setup) a na konci se puvodni obsah
vrati a overi (porovnani obsahu souboru). Vychozi je jedna deska z kazde
platformy (CircuitPython, MicroPython na Picu, micro:bit), --all-boards
otestuje vsechny pripojene.

Netestuji se (zamerne): cpy bootloader a cpy flash (meni firmware desky),
cpy wipe --format (preformatovani), cpy open (otevre okno spravce souboru),
cpy lib (potrebuje circup a internet; overi se jen hlaska, kdyz circup chybi).
"""
import argparse
import ctypes
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE.parents[1]
PY = sys.executable
IS_WIN = os.name == "nt"
ENV_KEYS = ("CIRCUITPY_PORT", "CIRCUITPY_PATH", "MICROPYTHON_PORT", "CPY_DEBUG")
CP_SYSTEM = {"System Volume Information", ".fseventsd", ".Trashes", ".Trash-1000",
             ".metadata_never_index", "boot_out.txt"}

MARK_CPY = "DESKA-TEST cpy koren spolecny jen_cpy"
MARK_PICO = "DESKA-TEST mpy koren spolecny jen_mpy balicek"
MARK_MICROBIT = "DESKA-TEST mpy koren bez-lib"


# ------------------------------------------------------------
# Vysledky
# ------------------------------------------------------------
class Results:
    def __init__(self):
        self.ok, self.failed, self.skipped = 0, [], []
        self.group = ""

    def check(self, name, cond, detail=""):
        full = f"{self.group}: {name}" if self.group else name
        if cond:
            self.ok += 1
            print(f"  OK    {name}")
        else:
            self.failed.append((full, detail))
            print(f"  CHYBA {name}")
            if detail:
                print("        " + detail.strip().replace("\n", "\n        ")[-1500:])
        return cond

    def skip(self, name, why):
        self.skipped.append((f"{self.group}: {name}", why))
        print(f"  --    {name} (preskoceno: {why})")

    def start(self, group):
        self.group = group
        print()
        print("=" * 70)
        print(group)
        print("=" * 70)


R = Results()


# ------------------------------------------------------------
# Zkusebni projekt
# ------------------------------------------------------------
FILES = {
    "code.py": (
        "import time\n"
        "import modul_koren\n"
        "import spolecny\n"
        "import jen_cpy\n"
        "print('DESKA-TEST cpy', modul_koren.ZNACKA, spolecny.ZNACKA, jen_cpy.ZNACKA)\n"
        "for i in range(15):\n"
        "    print(i, i * i)\n"
        "    time.sleep(0.1)\n"
        "print('DESKA-TEST konec')\n"),
    "main.py": (
        "import time\n"
        "import modul_koren\n"
        "try:\n"
        "    import spolecny\n"
        "    import jen_mpy\n"
        "    from balicek import cast\n"
        "    knihovny = spolecny.ZNACKA + ' ' + jen_mpy.ZNACKA + ' ' + cast.ZNACKA\n"
        "except ImportError:\n"
        "    knihovny = 'bez-lib'\n"
        "print('DESKA-TEST mpy ' + modul_koren.ZNACKA + ' ' + knihovny)\n"
        "for i in range(15):\n"
        "    print(str(i) + ', ' + str(i * i))\n"
        "    time.sleep_ms(100)\n"
        "print('DESKA-TEST konec')\n"),
    "modul_koren.py": "ZNACKA = 'koren'\n",
    "data.txt": "data pro program\n",
    "settings.toml": "# zkusebni nastaveni CircuitPythonu (prazdne)\n",
    "README.md": "# zkusebni projekt\n",
    "docs/navod.md": "navod\n",
    "lib/spolecny.py": (
        '"""Spolecna knihovna (lib/) - dlouhy dokumentacni retezec, aby se pri\n'
        'zmenseni (minify) bylo co zmensovat. Lorem ipsum dolor sit amet."""\n'
        "# komentar, ktery zmenseni odstrani\n"
        "ZNACKA = 'spolecny'\n\n\n"
        "def secti(prvni_cislo, druhe_cislo):\n"
        '    """Secte dve cisla."""\n'
        "    vysledek_souctu = prvni_cislo + druhe_cislo\n"
        "    return vysledek_souctu\n"),
    "lib_cpy/jen_cpy.py": "ZNACKA = 'jen_cpy'\n",
    "lib_mpy/jen_mpy.py": "ZNACKA = 'jen_mpy'\n",
    "lib_mpy/balicek/__init__.py": "",
    "lib_mpy/balicek/cast.py": "ZNACKA = 'balicek'\n",
    "lib/knihovna_c.mpy": b"C\x05" + b"\x00" * 30,      # hlavicka predprelozene knihovny CircuitPythonu
    "lib/knihovna_m.mpy": b"M\x06" + b"\x00" * 30,      # hlavicka predprelozene knihovny MicroPythonu
}

EXPECTED = {   # soubor v projektu -> cesta na desce
    "cpy": {"code.py": "code.py", "data.txt": "data.txt", "modul_koren.py": "modul_koren.py",
            "settings.toml": "settings.toml", "lib/spolecny.py": "lib/spolecny.py",
            "lib/knihovna_c.mpy": "lib/knihovna_c.mpy", "lib_cpy/jen_cpy.py": "lib/jen_cpy.py"},
    "pico": {"main.py": "main.py", "data.txt": "data.txt", "modul_koren.py": "modul_koren.py",
             "lib/spolecny.py": "lib/spolecny.py", "lib/knihovna_m.mpy": "lib/knihovna_m.mpy",
             "lib_mpy/jen_mpy.py": "lib/jen_mpy.py", "lib_mpy/balicek/__init__.py": "lib/balicek/__init__.py",
             "lib_mpy/balicek/cast.py": "lib/balicek/cast.py"},
    "microbit": {"main.py": "main.py", "data.txt": "data.txt", "modul_koren.py": "modul_koren.py"},
    "mpy": {"main.py": "main.py", "data.txt": "data.txt", "modul_koren.py": "modul_koren.py"},
}


def make_project(root):
    """Zkusebni projekt: nastroje ze sablony + vygenerovane soubory."""
    (root / ".vscode").mkdir(parents=True)
    for f in ("deska.py", "upload.toml", "settings.json"):
        shutil.copy2(TEMPLATE / ".vscode" / f, root / ".vscode" / f)
    shutil.copytree(TEMPLATE / "pc", root / "pc", ignore=shutil.ignore_patterns("__pycache__"))
    for rel, content in FILES.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            p.write_bytes(content)
        else:
            p.write_text(content, encoding="utf-8", newline="\n")
    return root


def clean_env(extra=None):
    env = {k: v for k, v in os.environ.items() if k not in ENV_KEYS}
    env.update(NO_COLOR="1", PYTHONIOENCODING="utf-8", MPLBACKEND="Agg")
    env.update(extra or {})
    return env


def run(proj, tool, *args, env=None, timeout=240):
    """Spusti deska.py v projektu proj. Vraci (navratovy kod, vystup)."""
    cmd = [PY, str(proj / ".vscode" / "deska.py"), tool, *args]
    try:
        r = subprocess.run(cmd, cwd=proj, env=clean_env(env), capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout, stdin=subprocess.DEVNULL)
        return r.returncode, r.stdout + r.stderr
    except subprocess.TimeoutExpired as e:
        out = (e.stdout or b"").decode("utf-8", "replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
        return -9, out + "\n[TIMEOUT]"


def run_for(proj, seconds, tool, *args, env=None):
    """Spusti prikaz, ktery bezi do Ctrl+C (monitor), na danou dobu a pak ho ukonci."""
    p = subprocess.Popen([PY, str(proj / ".vscode" / "deska.py"), tool, *args], cwd=proj, env=clean_env(env),
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
    chunks = []
    t = threading.Thread(target=lambda: chunks.extend(iter(lambda: p.stdout.read(1), b"")), daemon=True)
    t.start()
    time.sleep(seconds)
    p.kill()
    p.wait()
    t.join(2)
    return b"".join(chunks).decode("utf-8", "replace")


def files_listing(out):
    """Z vystupu 'files' vytahne {soubor: cesta na desce} z casti 'Nahraje se'."""
    res, on = {}, False
    for row in out.splitlines():
        if row.startswith("Nahraje se"):
            on = True
            continue
        if row.startswith("Vynecha se"):
            break
        if on and row.startswith("   ") and "  (" in row:
            left = row.strip().split("  (")[0]
            src, _, dst = left.partition(" -> ")
            res[src] = dst or src
    return res


def lock_dir(path, lock):
    """Slozka (falesny disk) jen pro cteni a zpet - zapis pak skonci Errno 13."""
    if IS_WIN:
        user = os.environ.get("USERNAME", "")
        if lock:
            subprocess.run(["icacls", str(path), "/deny", f"{user}:(OI)(CI)(WD,AD)"], capture_output=True)
        else:
            subprocess.run(["icacls", str(path), "/remove:d", user, "/T"], capture_output=True)
    else:
        for p in [path, *path.rglob("*")]:
            p.chmod(0o555 if lock and p.is_dir() else 0o444 if lock else 0o755 if p.is_dir() else 0o644)


def sha_tree(root, skip=()):
    out = {}
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root).as_posix()
        if p.is_file() and rel.split("/")[0] not in skip:
            out[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


# ------------------------------------------------------------
# Testy bez desky
# ------------------------------------------------------------
def offline_tests(proj):
    R.start("Bez desky: napoveda, devices, chybne prikazy")
    rc, out = run(proj, "help")
    R.check("deska.py help", rc == 0 and "mpy <prikaz>" in out, out)
    for tool in ("mpy", "cpy"):
        rc, out = run(proj, tool, "help")
        R.check(f"{tool} help", rc == 0 and "Pouziti:" in out and "files" in out, out)
        rc, out = run(proj, tool, "neexistuje")
        R.check(f"{tool} neznamy prikaz -> chyba", rc == 1 and "Neznamy prikaz" in out, out)
        rc, out = run(proj, tool, "files", "--blbost")
        R.check(f"{tool} neznama volba -> chyba", rc == 1 and "Neznama volba" in out, out)
    rc, out = run(proj, "devices")
    R.check("devices", rc == 0 and "CircuitPython" in out and "MicroPython" in out, out)
    rc, out = run(proj, "devices", "--json")
    try:
        data = json.loads(out)
        R.check("devices --json (platny JSON)", rc == 0 and "devices" in data, out)
    except ValueError:
        R.check("devices --json (platny JSON)", False, out)

    R.start("Bez desky: pravidla nahravani (files, upload.toml)")
    for profile, tool, args in (("cpy", "cpy", ()), ("pico", "mpy", ("pico",)),
                                ("microbit", "mpy", ("microbit",)), ("mpy", "mpy", ("mpy",))):
        rc, out = run(proj, tool, "files", *args)
        got = files_listing(out)
        R.check(f"{tool} files {' '.join(args)}: presne ocekavane soubory a cesty na desce",
                rc == 0 and got == EXPECTED[profile], f"ocekavano {EXPECTED[profile]}\ndostal    {got}\n{out}")
    rc, out = run(proj, "cpy", "files")
    R.check("cpy files: .mpy MicroPythonu vynechana podle hlavicky", "lib/knihovna_m.mpy  - vzdy vynechano - .mpy pro MicroPython" in out, out)
    rc, out = run(proj, "mpy", "files", "microbit")
    R.check("mpy files microbit: zadna slozka s knihovnami", "lib/  - nepovoleno" in out and "lib_mpy/  - nepovoleno" in out, out)
    rc, out = run(proj, "mpy", "files", "nesmysl")
    R.check("mpy files nesmysl -> chyba", rc == 1 and "Pouziti" in out, out)

    rules = proj / ".vscode" / "upload.toml"
    original = rules.read_text(encoding="utf-8")
    bad = {
        "chyba v zapisu TOML": ("[all]\nenable = [\"/*\"\n", "chyba v zapisu"),
        "neznama sekce": ("[vse]\nenable = [\"/*\"]\n", "neznama sekce [vse]"),
        "neznamy klic": ("[all]\nenabled = [\"/*\"]\n", "neznamy klic 'enabled'"),
        "hodnota neni seznam masek": ("[all]\nenable = 5\n", "musi byt seznam masek"),
        "pravidlo mimo sekci": ("enable = [\"/*\"]\n", "neni v zadne sekci"),
    }
    try:
        for name, (text, needle) in bad.items():
            rules.write_text(text, encoding="utf-8")
            rc, out = run(proj, "cpy", "files")
            R.check(f"upload.toml: {name} -> srozumitelna chyba", rc == 1 and needle in out and "Traceback" not in out, out)
        rules.unlink()
        rc, out = run(proj, "cpy", "files")
        R.check("upload.toml chybi -> srozumitelna chyba", rc == 1 and "Chybi soubor s pravidly" in out, out)
        # [micropython.microbit] je posledni sekce souboru - pridame do ni enable
        rules.write_text(original.rstrip() + '\nenable = ["lib/"]\n', encoding="utf-8")
        rc, out = run(proj, "mpy", "files", "microbit")
        R.check("micro:bit s povolenou slozkou lib/ -> upozorneni (nema slozky)",
                rc == 1 and "micro:bit nema slozky" in out, out)
    finally:
        rules.write_text(original, encoding="utf-8")
    dup = proj / "lib_mpy" / "spolecny.py"
    dup.write_text("ZNACKA = 'dvojce'\n", encoding="utf-8")
    try:
        rc, out = run(proj, "mpy", "files", "pico")
        R.check("lib/spolecny.py + lib_mpy/spolecny.py -> kolize na desce", rc == 1 and "stejnym jmenem lib/spolecny.py" in out, out)
        rc, out = run(proj, "cpy", "files")
        R.check("... na CircuitPython (lib_mpy nejde) kolize neni", rc == 0, out)
    finally:
        dup.unlink()
    old = proj / ".vscode" / "upload_config.txt"
    old.write_text("main.py\n", encoding="utf-8")
    rc, out = run(proj, "cpy", "files")
    R.check("stary upload_config.txt -> upozorneni, ze se nepouziva", rc == 0 and "upload_config.txt se uz nepouziva" in out, out)
    old.unlink()

    R.start("Bez desky: minify")
    settings = proj / ".vscode" / "deska.json"
    rc, out = run(proj, "mpy", "minify")
    R.check("mpy minify (stav, nahled velikosti)", rc == 0 and "na desku jde" in out, out)
    for level in ("simple", "full", "max", "off"):
        rc, out = run(proj, "mpy", "minify", level)
        val = json.loads(settings.read_text(encoding="utf-8")).get("minify", {}).get("mpy")
        R.check(f"mpy minify {level} -> deska.json", rc == 0 and val == (level if level != "off" else False), f"{val}\n{out}")
    rc, out = run(proj, "cpy", "minify", "max")
    R.check("cpy minify max -> chyba (jen mpy)", rc == 1, out)
    rc, out = run(proj, "cpy", "minify", "full")
    R.check("cpy minify full", rc == 0, out)
    run(proj, "cpy", "minify", "off")
    rc, out = run(proj, "mpy", "minify", "keep", "secti")
    keep = json.loads(settings.read_text(encoding="utf-8")).get("minify_keep")
    R.check("minify keep secti", rc == 0 and keep == ["secti"], f"{keep}\n{out}")
    rc, out = run(proj, "mpy", "minify", "keep", "1spatne")
    R.check("minify keep spatne jmeno -> chyba", rc == 1, out)
    rc, out = run(proj, "mpy", "minify", "unkeep", "secti")
    R.check("minify unkeep secti", rc == 0 and not json.loads(settings.read_text(encoding="utf-8")).get("minify_keep"), out)
    rc, out = run(proj, "mpy", "minify", "exclude", "lib/spolecny.py")
    R.check("minify exclude lib/spolecny.py", rc == 0 and "lib/spolecny.py" in settings.read_text(encoding="utf-8"), out)
    rc, out = run(proj, "mpy", "minify", "include", "lib/spolecny.py")
    R.check("minify include lib/spolecny.py", rc == 0 and "lib/spolecny.py" not in settings.read_text(encoding="utf-8"), out)
    settings.unlink(missing_ok=True)
    # uroven max: moduly, ktere main.py nepouziva, se nenahravaji
    (proj / "nepouzity.py").write_text("X = 1\n", encoding="utf-8")
    try:
        run(proj, "mpy", "minify", "max")
        for profile in ("microbit", "pico"):
            rc, out = run(proj, "mpy", "files", profile)
            got = files_listing(out)
            R.check(f"mpy files {profile} s max: nepouzity.py vynechan, pouzivane moduly a knihovny zustanou",
                    rc == 0 and got == EXPECTED[profile] and "nepouzity.py  - uroven max: main.py ho nepouziva" in out,
                    f"{got}\n{out}")
        run(proj, "mpy", "minify", "full")
        rc, out = run(proj, "mpy", "files", "microbit")
        R.check("mpy files s full: nepouzity.py se nahraje", rc == 0 and "nepouzity.py" in files_listing(out), out)
    finally:
        settings.unlink(missing_ok=True)
        (proj / "nepouzity.py").unlink()
    (proj / "boot.py").write_text("# boot\n", encoding="utf-8")
    try:
        rc, out = run(proj, "mpy", "files", "microbit")
        R.check("boot.py na micro:bit ne (MicroPython na micro:bitu ho nespousti)",
                "boot.py" not in files_listing(out) and 'boot.py  - disable "/boot.py" v [micropython.microbit]' in out, out)
        rc, out = run(proj, "mpy", "files", "pico")
        R.check("boot.py na Pico ano", "boot.py" in files_listing(out), out)
    finally:
        (proj / "boot.py").unlink()

    R.start("Bez desky: select, vscode, sim, test, lib, flash")
    for tool in ("cpy", "mpy"):
        rc, out = run(proj, tool, "select", "auto")
        R.check(f"{tool} select auto", rc == 0, out)
    active = proj / ".vscode" / ".active_device.json"
    rc, out = run(proj, "mpy", "select", "COM99")
    R.check("mpy select nepripojeneho portu -> ulozi se s upozornenim",
            rc == 0 and "neni pripojena" in out and "COM99" in active.read_text(encoding="utf-8"), out)
    rc, out = run(proj, "mpy", "select", "auto")
    R.check("mpy select auto -> vyber zrusen",
            rc == 0 and "COM99" not in (active.read_text(encoding="utf-8") if active.exists() else ""), out)
    rc, out = run(proj, "vscode")
    data = json.loads((proj / ".vscode" / "settings.json").read_text(encoding="utf-8"))
    R.check("vscode (panel a Run on Save v settings.json)", rc == 0 and "micropython.commands" in data
            and "emeraldwalk.runonsave" in data, out)
    rc, out = run(proj, "cpy", "sim", timeout=60)
    R.check("cpy sim: lib/ a lib_cpy/ v ceste, program dobehne", rc == 0 and MARK_CPY in out, out)
    rc, out = run(proj, "mpy", "sim", "--picoed", timeout=60)
    R.check("mpy sim --picoed: lib/ a lib_mpy/ v ceste, program dobehne", rc == 0 and MARK_PICO in out, out)
    rc, out = run(proj, "mpy", "sim", "--pico", timeout=60)
    R.check("mpy sim --pico", rc == 0 and MARK_PICO in out, out)
    rc, out = run(proj, "mpy", "sim", "--microbit", timeout=60)
    R.check("mpy sim --microbit: bez knihoven (micro:bit nema slozky), program dobehne",
            rc == 0 and MARK_MICROBIT in out and "BBC micro:bit" in out, out)
    # bez volby: podle pripojene desky (micro:bit -> micro:bit, jinak Pico:ed)
    rc, out = run(proj, "mpy", "sim", timeout=60)
    R.check("mpy sim bez volby: deska podle pripojene, program dobehne", rc == 0 and (
        (MARK_MICROBIT in out and "podle pripojene desky" in out)
        or (MARK_PICO in out and "Pico:ed v2 (vychozi" in out)), out)
    (proj / "sim_microbit.py").write_text(
        "from microbit import *\n"
        "import music\n"
        "import radio\n"
        "from neopixel import NeoPixel\n"
        "display.show(Image.HEART)\n"
        "display.scroll('Ahoj', delay=10)\n"
        "pin8.write_digital(1)\n"
        "music.play(music.BA_DING)\n"
        "radio.on()\n"
        "radio.send('zprava')\n"
        "np = NeoPixel(pin16, 1)\n"
        "np[0] = (255, 0, 0)\n"
        "np.show()\n", encoding="utf-8")
    rc, out = run(proj, "mpy", "sim", "sim_microbit.py", "--microbit", timeout=60)
    R.check("mpy sim --microbit: displej, piny, music, radio, neopixel v konzoli", rc == 0 and all(
        t in out for t in ("#####", 'Displej: text "Ahoj"', "Pin P8: 1", "melodie music.BA_DING",
                           'Radio: odeslano "zprava"', "NeoPixel: #ff0000")), out)
    rc, out = run(proj, "mpy", "sim", "sim_microbit.py", "--picoed", timeout=60)
    R.check("mpy sim --picoed: modul microbit neni (jako na Picu)",
            rc == 1 and "No module named 'microbit'" in out, out)
    (proj / "sim_microbit.py").unlink()
    (proj / "jen_v_cpy.py").write_text("import jen_mpy\n", encoding="utf-8")
    rc, out = run(proj, "cpy", "sim", "jen_v_cpy.py", timeout=60)
    R.check("cpy sim: knihovna z lib_mpy/ neni k dispozici (jako na desce)", rc == 1 and "jen_mpy" in out, out)
    (proj / "jen_v_cpy.py").unlink()
    # unit testy z pc/ testuji code.py a main.py sablony - spusti se na kopii sablony
    copy = proj.parent / "sablona"
    shutil.copytree(TEMPLATE, copy, ignore=shutil.ignore_patterns(".git", ".venv", "__pycache__"))
    try:
        for tool in ("cpy", "mpy"):
            rc, out = run(copy, tool, "test", timeout=120)
            R.check(f"{tool} test (unit testy sablony z pc/)", rc == 0 and "testy prosly" in out, out)
    finally:
        shutil.rmtree(copy, ignore_errors=True)
    rc, out = run(proj, "cpy", "lib", "list", env={"CIRCUITPY_PATH": str(proj)})
    if "Chybi nastroj circup" in out:
        R.check("cpy lib bez circup -> rada, jak ho nainstalovat", rc != 0 and "pip" in out, out)
    else:
        R.skip("cpy lib", "circup je nainstalovany - test potrebuje desku a internet")
    rc, out = run(proj, "cpy", "flash")
    R.check("cpy flash bez souboru -> chyba", rc == 1 and ".uf2" in out, out)
    rc, out = run(proj, "cpy", "flash", "neni.uf2")
    R.check("cpy flash neexistujici soubor -> chyba", rc == 1, out)

    R.start("Bez desky: zapis na falesny disk CIRCUITPY (slozka na PC)")
    fake = Path(tempfile.mkdtemp(prefix="deska_fake_circuitpy_"))
    env = {"CIRCUITPY_PATH": str(fake)}
    try:
        rc, out = run(proj, "cpy", "upload", env=env)
        got = {p.relative_to(fake).as_posix() for p in fake.rglob("*") if p.is_file()}
        R.check("cpy upload: na disku presne ocekavane soubory (lib_cpy/ -> lib/)",
                rc == 0 and got == set(EXPECTED["cpy"].values()), f"{sorted(got)}\n{out}")
        rc, out = run(proj, "cpy", "upload", env=env)
        R.check("cpy upload podruhe: vse aktualni", rc == 0 and "vse aktualni" in out, out)
        (proj / "lib_cpy" / "jen_cpy.py").write_text("ZNACKA = 'jen_cpy'\n# zmena\n", encoding="utf-8")
        rc, out = run(proj, "cpy", "save", "lib_cpy/jen_cpy.py", env=env)
        R.check("cpy save lib_cpy/jen_cpy.py -> lib/jen_cpy.py na disku",
                rc == 0 and "# zmena" in (fake / "lib" / "jen_cpy.py").read_text(encoding="utf-8"), out)
        rc, out = run(proj, "cpy", "save", "docs/navod.md", env=env)
        R.check("cpy save docs/navod.md -> nekopiruje se (slozka neni povolena)",
                rc == 0 and "NEKOPIRUJE SE" in out and not (fake / "docs").exists(), out)
        rc, out = run(proj, "cpy", "save", "main.py", env=env)
        R.check("cpy save main.py -> nekopiruje se (disable v [circuitpython])", rc == 0 and "NEKOPIRUJE SE" in out, out)
        (fake / "code.py").unlink()
        rc, out = run(proj, "cpy", "main", env=env)
        R.check("cpy main -> jen code.py", rc == 0 and (fake / "code.py").is_file(), out)
        run(proj, "cpy", "minify", "simple")
        rc, out = run(proj, "cpy", "upload", env=env)
        small = (fake / "lib" / "spolecny.py").stat().st_size < (proj / "lib" / "spolecny.py").stat().st_size
        R.check("cpy minify simple + upload -> knihovna na disku zmensena, code.py ne",
                rc == 0 and small and (fake / "code.py").read_bytes() == (proj / "code.py").read_bytes(), out)
        run(proj, "cpy", "minify", "off")
        rc, out = run(proj, "cpy", "list", env=env)
        R.check("cpy list", rc == 0 and "code.py" in out, out)
        rc, out = run(proj, "cpy", "wipe", "--yes", env=env)
        R.check("cpy wipe --yes -> disk prazdny", rc == 0 and not any(fake.iterdir()), out)
        rc, out = run(proj, "cpy", "setup", "--yes", env=env)
        got = {p.relative_to(fake).as_posix() for p in fake.rglob("*") if p.is_file()}
        R.check("cpy setup --yes -> projekt na disku", rc == 0 and got == set(EXPECTED["cpy"].values()), out)
        conflict = proj / "modul_koren.py"
        keep = conflict.read_text(encoding="utf-8")
        conflict.write_text("<<<<<<< HEAD\nZNACKA = 'a'\n=======\nZNACKA = 'b'\n>>>>>>> vetev\n", encoding="utf-8")
        rc, out = run(proj, "cpy", "upload", env=env)
        R.check("cpy upload s konfliktem z gitu -> zastavi v kroku 1", rc == 1 and "konflikt z gitu" in out, out)
        conflict.write_text(keep, encoding="utf-8")
        # disk jen pro cteni: automaticky restart se zkusi, ale port COM99 neexistuje -> rady
        (proj / "code.py").write_text(FILES["code.py"] + "# zmena pro zapis\n", encoding="utf-8")
        lock_dir(fake, True)
        try:
            rc, out = run(proj, "cpy", "save", "code.py", env={**env, "CIRCUITPY_PORT": "COM99",
                                                              "DESKA_AUTO_RESTART_PAUSE": "0"})
            R.check("cpy save na disk jen pro cteni -> zkusi restart, bez portu poradi (reset --hard, napajeni)",
                    rc == 1 and "je jen pro cteni; automaticky restart desky nejde" in out
                    and "cpy reset --hard" in out and "napajeni" in out, out)
            rc, out = run(proj, "cpy", "upload", env={**env, "CIRCUITPY_PORT": "COM99",
                                                     "DESKA_AUTO_RESTART_PAUSE": "0"})
            R.check("cpy upload na disk jen pro cteni -> stejne (jeden pokus o restart)",
                    rc == 1 and out.count("automaticky restart desky nejde") == 1 and "napajeni" in out, out)
        finally:
            lock_dir(fake, False)
            (proj / "code.py").write_text(FILES["code.py"], encoding="utf-8")
    finally:
        shutil.rmtree(fake, ignore_errors=True)
        (proj / "lib_cpy" / "jen_cpy.py").write_text(FILES["lib_cpy/jen_cpy.py"], encoding="utf-8")


# ------------------------------------------------------------
# Desky: zaloha a obnova
# ------------------------------------------------------------
def cp_backup(drive, dest):
    for e in drive.iterdir():
        if e.name in CP_SYSTEM:
            continue
        (shutil.copytree if e.is_dir() else shutil.copy2)(e, dest / e.name)
    return sha_tree(dest)


def cp_clear(drive):
    for e in drive.iterdir():
        if e.name in CP_SYSTEM:
            continue
        if e.is_dir():
            shutil.rmtree(e)
        else:
            e.unlink()


def cp_restore(drive, backup):
    cp_clear(drive)
    for e in backup.iterdir():
        (shutil.copytree if e.is_dir() else shutil.copy2)(e, drive / e.name)
    return sha_tree(drive, skip=CP_SYSTEM)


MP_LIST_CODE = """
import os
r = []
def w(p):
    for n in (os.listdir(p) if p else os.listdir()):
        f = p + '/' + n if p else n
        try:
            st = os.stat(f)
        except OSError:
            continue
        if st[0] & 0x4000:
            r.append((f, -1))
            w(f)
        else:
            r.append((f, st[6]))
w('')
print('@@' + repr(r))
"""


def mpremote(port, *args, tries=4):
    last = None
    for _ in range(tries):
        last = subprocess.run([PY, "-m", "mpremote", "connect", port, *args], capture_output=True,
                              text=True, encoding="utf-8", errors="replace", timeout=120)
        if last.returncode == 0:
            return last
        time.sleep(0.5)
    raise RuntimeError(f"mpremote {' '.join(args)} selhal: {last.stdout}{last.stderr}")


def wait_port(port, seconds=45):
    """Pocka, az deska na portu odpovida (napr. po reset --hard se znovu
    pripoji na USB). Vraci True / False."""
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        r = subprocess.run([PY, "-m", "mpremote", "connect", port, "exec", "pass"], capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=60)
        if r.returncode == 0:
            return True
        time.sleep(1)
    return False


def mp_list(port):
    import ast
    out = mpremote(port, "exec", MP_LIST_CODE).stdout
    row = [x for x in out.splitlines() if x.startswith("@@")][-1]
    return ast.literal_eval(row[2:])


def mp_backup(port, dest, quiet=False):
    """Stahne vse z desky do dest. Soubor s prazdnym jmenem (na micro:bitu
    vznikne po 'mpremote cp soubor :') nema na desce zadny vyznam - nezalohuje
    se, test ho smaze (wipe) a neobnovi."""
    entries = mp_list(port)
    if any(path == "" for path, _ in entries) and not quiet:
        print("  pozor: na desce je soubor s prazdnym jmenem - nema vyznam, po testu uz na desce nebude")
    entries = [(path, size) for path, size in entries if path]
    for path, size in entries:
        if size < 0:
            (dest / path).mkdir(parents=True, exist_ok=True)
    for path, size in entries:
        if size >= 0:
            (dest / path).parent.mkdir(parents=True, exist_ok=True)
            mpremote(port, "cp", ":" + path, str(dest / path))
    return entries, sha_tree(dest)


def mp_restore(port, backup, entries, proj):
    if not wait_port(port, 60):
        raise RuntimeError(f"deska na {port} neodpovida - odpoj a pripoj ji a obnov zalohu {backup}")
    rc, out = run(proj, "mpy", "wipe", "--yes", env={"MICROPYTHON_PORT": port})
    if rc != 0:
        raise RuntimeError(f"mpy wipe pred obnovou selhal:\n{out}")
    for path, size in entries:
        if size < 0:
            mpremote(port, "mkdir", ":" + path)
    for path, size in entries:
        if size >= 0:
            mpremote(port, "cp", str(backup / path), ":" + path)
    check = Path(tempfile.mkdtemp(prefix="deska_overeni_"))
    try:
        return mp_backup(port, check, quiet=True)[1]
    finally:
        shutil.rmtree(check, ignore_errors=True)


# ------------------------------------------------------------
# REPL pres novou konzoli (Windows): posle 1+1, Enter, Ctrl+C, Ctrl+]
# ------------------------------------------------------------
def repl_test(proj, tool, env):
    if not IS_WIN:
        return None, "jen ve Windows (klavesy se posilaji do nove konzole)"
    import ctypes.wintypes as w
    k = ctypes.windll.kernel32
    marker = Path(tempfile.mkdtemp(prefix="deska_repl_")) / "after.txt"
    cmd = f'cmd /c ""{PY}" "{proj / ".vscode" / "deska.py"}" {tool} repl & echo AFTER> "{marker}""'
    p = subprocess.Popen(cmd, cwd=proj, env=clean_env(env), creationflags=subprocess.CREATE_NEW_CONSOLE)
    time.sleep(10)

    class KEY(ctypes.Structure):
        _fields_ = [("bKeyDown", w.BOOL), ("wRepeatCount", w.WORD), ("wVirtualKeyCode", w.WORD),
                    ("wVirtualScanCode", w.WORD), ("UnicodeChar", w.WCHAR), ("dwControlKeyState", w.DWORD)]

    class REC(ctypes.Structure):
        _fields_ = [("EventType", w.WORD), ("_pad", w.WORD), ("Event", KEY)]

    class COORD(ctypes.Structure):
        _fields_ = [("X", w.SHORT), ("Y", w.SHORT)]

    class CSBI(ctypes.Structure):
        _fields_ = [("dwSize", COORD), ("dwCursorPosition", COORD), ("wAttributes", w.WORD),
                    ("srWindow", w.SMALL_RECT), ("dwMaximumWindowSize", COORD)]

    k.FreeConsole()
    if not k.AttachConsole(p.pid):
        p.kill()
        return False, "AttachConsole selhal"
    try:
        hin = k.CreateFileW("CONIN$", 0xC0000000, 3, None, 3, 0, None)
        hout = k.CreateFileW("CONOUT$", 0xC0000000, 3, None, 3, 0, None)

        def send(ch, vk, ctrl=False):
            recs = (REC * 2)()
            for i, down in enumerate((True, False)):
                recs[i].EventType = 1
                recs[i].Event = KEY(down, 1, vk, 0, ch, 0x0008 if ctrl else 0)
            n = w.DWORD()
            k.WriteConsoleInputW(hin, recs, 2, ctypes.byref(n))
            time.sleep(0.4)

        for c in "1+1":
            send(c, ord(c) if c.isdigit() else 0xBB)
        send("\r", 0x0D)
        time.sleep(1)
        send("\x03", ord("C"), ctrl=True)
        time.sleep(1.5)
        send("\x1d", 0xDD, ctrl=True)
        time.sleep(5)
        info = CSBI()
        k.GetConsoleScreenBufferInfo(hout, ctypes.byref(info))
        width, rows = info.dwSize.X, info.dwCursorPosition.Y + 1
        lines_read = []
        for y in range(rows):                   # po radcich: siroky znak (emoji) by posunul deleni
            buf = ctypes.create_unicode_buffer(width + 1)
            n = w.DWORD()
            k.ReadConsoleOutputCharacterW(hout, buf, width, COORD(0, y), ctypes.byref(n))
            lines_read.append(buf.value[:n.value].rstrip())
        text = "\n".join(lines_read)
        if p.poll() is None and "Terminate batch job" in text:
            send("y", ord("Y"))
            send("\r", 0x0D)
    finally:
        k.FreeConsole()
    time.sleep(1)
    if p.poll() is None:
        p.kill()
    lines = [x.strip() for x in text.splitlines()]
    ok = "2" in lines and "Terminate batch job" not in text and "REPL ukoncen" in text and marker.exists()
    shutil.rmtree(marker.parent, ignore_errors=True)
    return ok, text


# ------------------------------------------------------------
# Desky: prubeh testu
# ------------------------------------------------------------
# Zamceni disku CIRCUITPY pro PC: boot.py prepne uloziste do zapisu pro program
# (storage.remount), pro PC je pak disk jen pro cteni. Volani je zapsane tak,
# aby ho pojistka v deska.py (hleda "remount" v boot.py) nepoznala - test tak
# projde skutecnym automatickym restartem.
LOCK_BOOT_PY = 'import storage\ngetattr(storage, "re" + "mount")("/", readonly=False)\n'
# Zamceni, ktere po restartu pomine: boot.py disk zamkne a hned se smaze
# (po zamceni smi zapisovat program). Pri dalsim startu uz neni - jako kdyz
# se deska "zasekne" do jen pro cteni a restart ji spravi.
LOCK_ONCE_BOOT_PY = LOCK_BOOT_PY + 'import os\nos.remove("/boot.py")\n'


def cp_lock(proj, env, drive, boot_py):
    """Zapise zamykaci boot.py a restartuje desku. Vraci True, kdyz je disk pak pro PC jen pro cteni."""
    (drive / "boot.py").write_text(boot_py, encoding="utf-8")
    run(proj, "cpy", "reset", "--hard", env=env)
    time.sleep(3)
    return wait_drive(drive, 45) and not drive_writable(drive)


def drive_writable(drive):
    probe = drive / "_deska_test_zapis.tmp"
    try:
        probe.write_bytes(b"x")
        probe.unlink()
        return True
    except OSError:
        return False


def cp_serial_exec(port, lines):
    """Zastavi program (Ctrl+C) a v REPL desky napise radky (bez cekani na vysledek)."""
    import serial
    with serial.Serial(port, 115200, timeout=0.3) as ser:
        ser.write(b"\x03\x03")
        time.sleep(1)
        ser.write(b"\r")
        time.sleep(0.5)
        ser.read(4096)
        for row in lines:
            ser.write(row.encode() + b"\r")
            time.sleep(0.4)


def cp_unlock(port, drive):
    """Smaze zamykaci boot.py (program na desce zapisovat muze) a restartuje desku."""
    if not (drive / "boot.py").is_file():
        return drive_writable(drive)
    cp_serial_exec(port, ["import os", "os.remove('/boot.py')", "import microcontroller",
                          "microcontroller.reset()"])
    time.sleep(4)
    end = time.monotonic() + 40
    while time.monotonic() < end:
        if drive.exists() and drive_writable(drive):
            return True
        time.sleep(1)
    return False


def wait_drive(drive, seconds=30):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        if drive.exists():
            time.sleep(1)
            return True
        time.sleep(0.5)
    return False


def hw_circuitpython(proj, dev):
    drive, port = Path(dev["drive"]), dev["port"]
    R.start(f"CircuitPython {dev['name']} ({port}, {drive})")
    env = {"CIRCUITPY_PATH": str(drive), "CIRCUITPY_PORT": port}
    probe = drive / "_deska_test_zapis.tmp"     # disk muze byt pro PC jen pro cteni
    try:
        probe.write_bytes(b"x")
        probe.unlink()
    except OSError as e:
        R.skip("testy na teto desce", f"na disk {drive} nejde zapisovat ({e}) - deska zustava beze zmeny")
        return
    backup = Path(tempfile.mkdtemp(prefix="deska_zaloha_cpy_"))
    before = cp_backup(drive, backup)
    print(f"  zaloha: {len(before)} souboru -> {backup}")
    try:
        rc, out = run(proj, "cpy", "check", env=env)
        R.check("cpy check", rc == 0, out)
        rc, out = run(proj, "cpy", "list", env=env)
        R.check("cpy list", rc == 0, out)
        rc, out = run(proj, "cpy", "upload", env=env)
        got = {p.relative_to(drive).as_posix() for p in drive.rglob("*") if p.is_file()
               and p.relative_to(drive).parts[0] not in CP_SYSTEM}
        R.check("cpy upload: na desce ocekavane soubory", rc == 0 and set(EXPECTED["cpy"].values()) <= got
                and "main.py" not in got and "lib/jen_mpy.py" not in got, f"{sorted(got)}\n{out}")
        rc, out = run(proj, "cpy", "upload", env=env)
        R.check("cpy upload podruhe: vse aktualni", rc == 0 and "vse aktualni" in out, out)
        rc, out = run(proj, "cpy", "reset", env=env)
        R.check("cpy reset: program bezi a nasel knihovny z lib/ i lib_cpy/", rc == 0 and MARK_CPY in out, out)
        rc, out = run(proj, "cpy", "runmain", env=env, timeout=60)
        R.check("cpy runmain (z RAM)", rc == 0 and MARK_CPY in out, out)
        rc, out = run(proj, "cpy", "stop", env=env)
        R.check("cpy stop", rc == 0, out)
        out = run_for(proj, 8, "cpy", "monitor", "--restart", env=env)
        R.check("cpy monitor --restart (8 s)", MARK_CPY in out, out)
        rc, out = run(proj, "cpy", "plot", "--seconds=3", env=env, timeout=150)
        R.check("cpy plot --seconds=3", rc == 0, out)
        (proj / "lib_cpy" / "jen_cpy.py").write_text("ZNACKA = 'jen_cpy'\n# save\n", encoding="utf-8")
        rc, out = run(proj, "cpy", "save", "lib_cpy/jen_cpy.py", env=env)
        R.check("cpy save lib_cpy/jen_cpy.py -> lib/jen_cpy.py na desce",
                rc == 0 and "# save" in (drive / "lib" / "jen_cpy.py").read_text(encoding="utf-8"), out)
        (proj / "lib_cpy" / "jen_cpy.py").write_text(FILES["lib_cpy/jen_cpy.py"], encoding="utf-8")
        rc, out = run(proj, "cpy", "main", "--all", "--watch", env=env)
        R.check("cpy main --all --watch (zapise code.py a program se spusti)", rc == 0 and MARK_CPY in out, out)
        run(proj, "cpy", "minify", "simple")
        rc, out = run(proj, "cpy", "upload", "--stop", env=env)
        small = (drive / "lib" / "spolecny.py").stat().st_size < (proj / "lib" / "spolecny.py").stat().st_size
        rc2, out2 = run(proj, "cpy", "reset", env=env)
        R.check("cpy minify simple + upload --stop -> zmensena knihovna a program bezi",
                rc == 0 and small and MARK_CPY in out2, out + out2)
        run(proj, "cpy", "minify", "off")
        rc, out = run(proj, "cpy", "wipe", "--yes", env=env)
        left = [e.name for e in drive.iterdir() if e.name not in CP_SYSTEM]
        R.check("cpy wipe --yes -> deska prazdna", rc == 0 and not left, f"{left}\n{out}")
        rc, out = run(proj, "cpy", "setup", "--yes", env=env)
        rc2, out2 = run(proj, "cpy", "reset", env=env)
        R.check("cpy setup --yes -> projekt na desce a bezi", rc == 0 and MARK_CPY in out2, out + out2)
        rc, out = run(proj, "cpy", "select", str(drive), env={})
        rc2, out2 = run(proj, "cpy", "select", "auto")
        R.check("cpy select <disk> a select auto", rc == 0 and rc2 == 0, out + out2)
        ok, text = repl_test(proj, "cpy", env)
        if ok is None:
            R.skip("cpy repl", text)
        else:
            R.check("cpy repl (1+1, Ctrl+C, Ctrl+])", ok, text)
        # disk jen pro cteni, ktery restart spravi -> automaticky restart a zapis projde
        auto = {**env, "DESKA_AUTO_RESTART_PAUSE": "0"}
        for cmd in (("save", "code.py"), ("upload",)):
            locked = cp_lock(proj, env, drive, LOCK_ONCE_BOOT_PY)
            R.check(f"zamceni disku, ktere po restartu pomine (pred cpy {cmd[0]})", locked)
            if not locked:
                continue
            mark = f"# zmena {cmd[0]}\n"
            (proj / "code.py").write_text(FILES["code.py"] + mark, encoding="utf-8")
            rc, out = run(proj, "cpy", *cmd, env=auto)
            on_board = (drive / "code.py").read_text(encoding="utf-8", errors="replace") if drive.exists() else ""
            R.check(f"cpy {cmd[0]} na zamceny disk -> automaticky restart a zapis projde",
                    rc == 0 and "restartuji celou desku" in out and "deska restartovana" in out
                    and mark in on_board and drive_writable(drive), out)
        (proj / "code.py").write_text(FILES["code.py"], encoding="utf-8")
        # disk jen pro cteni, ktery restart nespravi (boot.py zamkne disk pri kazdem startu)
        locked = cp_lock(proj, env, drive, LOCK_BOOT_PY)
        R.check("zamceni disku pres boot.py (disk je pro PC jen pro cteni)", locked)
        if locked:
            (proj / "code.py").write_text(FILES["code.py"] + "# zmena\n", encoding="utf-8")
            rc, out = run(proj, "cpy", "save", "code.py", env={**env, "DESKA_AUTO_RESTART_PAUSE": "0"})
            R.check("cpy save na zamceny disk -> automaticky restart, deska se vrati, zapis znovu, "
                    "pak rada odpojit napajeni",
                    rc == 1 and "restartuji celou desku" in out and "deska restartovana" in out
                    and "automaticky restart desky nepomohl" in out and "napajeni" in out, out)
            rc, out = run(proj, "cpy", "save", "code.py", env={**env, "DESKA_AUTO_RESTART_PAUSE": "600"})
            R.check("cpy save hned znovu -> restart se neopakuje (pojistka proti restartum dokola)",
                    rc == 1 and "znovu to nezkousim" in out and "restartuji celou desku" not in out, out)
            (proj / "code.py").write_text(FILES["code.py"], encoding="utf-8")
        R.check("odemceni disku (boot.py smazan pres REPL, restart)", cp_unlock(port, drive))
    except Exception:
        R.check("bez neocekavane chyby testu", False, traceback.format_exc())
    finally:
        wait_drive(drive)
        boot = drive / "boot.py"
        if (boot.is_file() and boot.read_text(errors="replace") in (LOCK_BOOT_PY, LOCK_ONCE_BOOT_PY)) \
                or not drive_writable(drive):
            cp_unlock(port, drive)
        after = cp_restore(drive, backup)
        R.check("OBNOVA: obsah desky stejny jako pred testem", after == before,
                f"pred {len(before)}, po {len(after)}: {set(before.items()) ^ set(after.items())}")
        if after == before:
            shutil.rmtree(backup, ignore_errors=True)
        else:
            print(f"  ZALOHA ZUSTALA: {backup}")
        # reset --hard az po obnove: deska se pri nem odpoji z USB a znovu pripoji. Kdyby to
        # Windows nezvladl (stalo se u Pica s MicroPythonem), ma deska aspon svuj puvodni obsah.
        rc, out = run(proj, "cpy", "reset", "--hard", env=env)
        time.sleep(3)
        back = wait_drive(drive, 45)
        rc2, out2 = run(proj, "cpy", "reset", env=env) if back else (1, "deska se nepripojila")
        R.check("cpy reset --hard (po obnove; deska se znovu pripoji a program bezi)",
                rc == 0 and back and rc2 == 0, out + out2)


def hw_micropython(proj, dev, profile):
    port = dev["port"]
    mark = MARK_MICROBIT if profile == "microbit" else MARK_PICO
    R.start(f"MicroPython {dev['name']} ({port}, pravidla {profile})")
    env = {"MICROPYTHON_PORT": port}
    backup = Path(tempfile.mkdtemp(prefix="deska_zaloha_mpy_"))
    entries, before = mp_backup(port, backup)
    print(f"  zaloha: {len(before)} souboru -> {backup}")
    expected = set(EXPECTED[profile].values())
    try:
        rc, out = run(proj, "mpy", "check", env=env)
        R.check("mpy check", rc == 0, out)
        rc, out = run(proj, "mpy", "list", env=env)
        R.check("mpy list", rc == 0, out)
        rc, out = run(proj, "mpy", "upload", env=env)
        got = {p for p, s in mp_list(port) if s >= 0}
        foreign = {"code.py", "settings.toml", "lib/jen_cpy.py", "lib/knihovna_c.mpy", "README.md"}
        # upload soubory, ktere na desce uz byly, nemaze - presnou shodu overi az setup
        R.check("mpy upload: ocekavane soubory na desce, zadne z jine platformy",
                rc == 0 and expected <= got and not (foreign & got),
                f"ocekavano {sorted(expected)}\nna desce  {sorted(got)}\n{out}")
        rc, out = run(proj, "mpy", "upload", env=env)
        R.check("mpy upload podruhe: vse beze zmeny", rc == 0 and "nahrano 0" in out, out)
        rc, out = run(proj, "mpy", "reset", env=env)
        R.check("mpy reset: program bezi" + (" bez knihoven ze slozek" if profile == "microbit"
                                             else " a nasel lib/ i lib_mpy/"), rc == 0 and mark in out, out)
        rc, out = run(proj, "mpy", "runmain", env=env, timeout=90)
        R.check("mpy runmain (z RAM)", rc == 0 and mark in out, out)
        rc, out = run(proj, "mpy", "main", env=env)
        R.check("mpy main", rc == 0, out)
        run(proj, "mpy", "minify", "full")
        rc, out = run(proj, "mpy", "upload", env=env)
        rc2, out2 = run(proj, "mpy", "reset", env=env)
        R.check("mpy minify full + upload -> program bezi", rc == 0 and mark in out2, out + out2)
        # max slucuje jen 'from modul import jmeno' na nejvyssi urovni - vlastni program
        main = proj / "main.py"
        main.write_text("from modul_koren import ZNACKA\nprint('DESKA-TEST max ' + ZNACKA)\n", encoding="utf-8")
        run(proj, "mpy", "minify", "max")
        rc, out = run(proj, "mpy", "upload", env=env)
        rc2, out2 = run(proj, "mpy", "reset", env=env)
        main.write_text(FILES["main.py"], encoding="utf-8")
        R.check("mpy minify max + upload -> sloucene main.py bezi",
                rc == 0 and "slouceni:" in out and "DESKA-TEST max koren" in out2, out + out2)
        run(proj, "mpy", "minify", "off")
        rc, out = run(proj, "mpy", "upload", env=env)
        R.check("mpy upload po vypnuti zmenseni", rc == 0, out)
        conflict = proj / "modul_koren.py"
        conflict.write_text("<<<<<<< HEAD\nZNACKA = 'a'\n=======\nZNACKA = 'b'\n>>>>>>> vetev\n", encoding="utf-8")
        rc, out = run(proj, "mpy", "upload", env=env)
        conflict.write_text(FILES["modul_koren.py"], encoding="utf-8")
        R.check("mpy upload s konfliktem z gitu -> zastavi pred nahranim", rc == 1 and "konflikt z gitu" in out, out)
        rc, out = run(proj, "mpy", "wipe", "--yes", env=env)
        R.check("mpy wipe --yes -> deska prazdna", rc == 0 and not mp_list(port), out)
        rc, out = run(proj, "mpy", "setup", "--yes", env=env)
        got = {p for p, s in mp_list(port) if s >= 0}
        R.check("mpy setup --yes -> projekt na desce", rc == 0 and got == expected, out)
        rc, out = run(proj, "mpy", "plot", "--seconds=3", env=env, timeout=150)
        R.check("mpy plot --seconds=3", rc == 0, out)
        rc, out = run(proj, "mpy", "select", port)
        rc2, out2 = run(proj, "mpy", "select", "auto")
        R.check("mpy select <port> a select auto", rc == 0 and rc2 == 0, out + out2)
        ok, text = repl_test(proj, "mpy", env)
        if ok is None:
            R.skip("mpy repl", text)
        else:
            R.check("mpy repl (1+1, Ctrl+C, Ctrl+])", ok, text)
    except Exception:
        R.check("bez neocekavane chyby testu", False, traceback.format_exc())
    finally:
        try:
            after = mp_restore(port, backup, entries, proj)
        except Exception as e:                  # noqa: BLE001
            after = None
            print(f"  OBNOVA SELHALA: {e}")
        R.check("OBNOVA: obsah desky stejny jako pred testem", after == before,
                f"pred {len(before)}, po {len(after or {})}: "
                f"{set(before.items()) ^ set((after or {}).items())}\nzaloha: {backup}")
        if after == before:
            shutil.rmtree(backup, ignore_errors=True)
        else:
            print(f"  ZALOHA ZUSTALA: {backup}")
        # reset --hard az po obnove: Pico se pri nem odpoji z USB a znovu pripoji. Kdyby to
        # Windows nezvladl (stalo se 2026-11-28, chyba 43), ma deska aspon svuj puvodni obsah.
        rc, out = run(proj, "mpy", "reset", "--hard", env=env)
        time.sleep(2)
        back = wait_port(port, 45)
        rc2, out2 = run(proj, "mpy", "reset", env=env) if back else (1, "deska se nepripojila")
        R.check("mpy reset --hard (po obnove; deska se znovu pripoji a program bezi)",
                rc == 0 and back and rc2 == 0, out + out2)


def hw_tests(proj, all_boards, only):
    rc, out = run(proj, "devices", "--json")
    devices = json.loads(out)["devices"]
    chosen = {"cpy": [], "pico": [], "microbit": []}
    for d in devices:
        if d["platform"] == "circuitpython" and d.get("drive") and d.get("port"):
            chosen["cpy"].append(d)
        elif d["platform"] == "micropython" and d.get("port"):
            usb = (d.get("usb") or "").upper()
            if usb == "0D28:0204":
                chosen["microbit"].append(d)
            elif usb.startswith("2E8A:"):
                chosen["pico"].append(d)
    for kind, devs in chosen.items():
        if only and kind not in only:
            continue
        if not devs:
            R.start(f"Deska {kind}")
            R.skip(f"testy na desce {kind}", "zadna takova deska neni pripojena")
            continue
        for dev in devs if all_boards else devs[:1]:
            if kind == "cpy":
                hw_circuitpython(proj, dev)
            else:
                hw_micropython(proj, dev, kind)


def main():
    ap = argparse.ArgumentParser(description="Testy prikazu deska.py (cpy, mpy)")
    ap.add_argument("--hw", action="store_true", help="testovat i na pripojenych deskach (se zalohou a obnovou)")
    ap.add_argument("--all-boards", action="store_true", help="vsechny pripojene desky, ne jen jednu z kazde platformy")
    ap.add_argument("--only", nargs="*", choices=("offline", "cpy", "pico", "microbit"),
                    help="jen nektere casti (offline = testy bez desky)")
    args = ap.parse_args()
    only = set(args.only or [])
    t0 = time.monotonic()
    tmp = Path(tempfile.mkdtemp(prefix="deska_test_projekt_"))
    proj = make_project(tmp / "projekt")
    print(f"Zkusebni projekt: {proj}")
    try:
        if not only or "offline" in only:
            offline_tests(proj)
        if args.hw:
            hw_tests(proj, args.all_boards, only - {"offline"})
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print()
    print("=" * 70)
    print(f"Vysledek: {R.ok} OK, {len(R.failed)} chyb, {len(R.skipped)} preskoceno "
          f"({time.monotonic() - t0:.0f} s)")
    for name, _detail in R.failed:
        print(f"  CHYBA: {name}")
    for name, why in R.skipped:
        print(f"  preskoceno: {name} - {why}")
    return 1 if R.failed else 0


if __name__ == "__main__":
    sys.exit(main())
