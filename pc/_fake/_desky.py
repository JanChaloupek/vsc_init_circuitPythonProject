# _fake/_desky.py

"""
Simulovaná deska MicroPythonu (mpy sim, mpy test).

Každá deska má jiné moduly. Na Pico:ed a Raspberry Pi Pico je modul
machine s Pin, I2C, PWM a Timer (falešný machine.py). Na BBC micro:bitu
je modul microbit (piny, displej, tlačítka) a k němu music, neopixel,
radio a malý machine (soubory microbit*.py). Tento modul určuje, které
falešné moduly program uvidí:

    nastav("picoed")     ELECFREAKS Pico:ed v2  (výchozí)
    nastav("pico")       Raspberry Pi Pico
    nastav("microbit")   BBC micro:bit v2

Program pak běží stejně jako na desce: `import microbit` na Picu skončí
chybou ImportError a `from machine import Pin` na micro:bitu taky.
Knihovny ze složek lib/ a lib_mpy/ jsou vidět jen na deskách, kam se
nahrávají (micro:bit žádné nemá - viz .vscode/upload.toml).

V testu si deskou může vybrat každý test sám (v setUp):

    from _fake._desky import nastav as nastav_desku
    nastav_desku("microbit")

Před dalším testem se deska vrátí na výchozí (mpy test).
Při změně desky se moduly projektu (např. vlastní knihovna studenta)
načtou znovu, aby nedržely objekty předchozí desky.
"""

import importlib
import sys
from pathlib import Path

try:
    from . import _rezim
except ImportError:
    import _rezim

DESKY = {
    "picoed": "ELECFREAKS Pico:ed v2",
    "pico": "Raspberry Pi Pico",
    "microbit": "BBC micro:bit v2",
}

# jmeno modulu v programu -> falesny modul v _fake
_MODULY = {
    "rp2040": {"machine": "machine"},
    "microbit": {"microbit": "microbit", "music": "microbit_music", "neopixel": "microbit_neopixel",
                 "radio": "microbit_radio", "machine": "microbit_machine"},
}

vychozi = "picoed"      # deska, na kterou se vraci pred kazdym testem
_projekt = None         # koren projektu (jeho moduly se po zmene desky nactou znovu)
_knihovny = {}          # deska -> slozky s knihovnami v sys.path (jako /lib na desce)


def priprav(projekt, knihovny, deska="picoed"):
    """Zavola deska.py: koren projektu, slozky knihoven pro kazdou desku
    a vychozi deska. Rovnou ji nastavi."""
    global _projekt, _knihovny, vychozi
    _projekt = Path(projekt).resolve()
    _knihovny = {d: [str(Path(c)) for c in cesty] for d, cesty in knihovny.items()}
    vychozi = deska
    nastav(deska)


def _rodina(deska):
    return "microbit" if deska == "microbit" else "rp2040"


def _zapomen_moduly_projektu():
    """Smaze ze sys.modules moduly z projektu (krome pc/ a skrytych slozek
    .vscode, .venv) - pri dalsim importu se nactou znovu pro novou desku."""
    if _projekt is None:
        return
    for jmeno, modul in list(sys.modules.items()):
        soubor = getattr(modul, "__file__", None)
        if not soubor:
            continue
        try:
            cast = Path(soubor).resolve().relative_to(_projekt).parts
        except (ValueError, OSError):
            continue
        if cast and (cast[0] == "pc" or cast[0].startswith(".")):
            continue
        del sys.modules[jmeno]


def _nastav_cesty(deska):
    """Slozky knihoven v sys.path: jen ty, ktere se nahravaji na desku."""
    vsechny = {c for cesty in _knihovny.values() for c in cesty}
    sys.path[:] = [c for c in sys.path if c not in vsechny]
    projekt = str(_projekt) if _projekt else None
    i = sys.path.index(projekt) + 1 if projekt in sys.path else 0
    sys.path[i:i] = _knihovny.get(deska, [])
    importlib.invalidate_caches()


def nastav(deska):
    """Prepne simulovanou desku ("picoed", "pico", "microbit")."""
    if deska not in DESKY:
        raise ValueError(f"Neznama deska: {deska} (" + ", ".join(DESKY) + ")")
    if deska == _rezim.deska:
        return
    for moduly in _MODULY.values():
        for jmeno in moduly:
            sys.modules.pop(jmeno, None)
    _zapomen_moduly_projektu()
    _nastav_cesty(deska)
    _rezim.zrus_tlacitka()
    _rezim.deska = deska
    balicek = __package__ or ""
    for jmeno, modul in _MODULY[_rodina(deska)].items():
        sys.modules[jmeno] = importlib.import_module(("." if balicek else "") + modul, balicek or None)
    if _rodina(deska) == "rp2040":
        sys.modules["machine"].nastav_desku(deska)
        # lib_mpy/picoed_v2_lib: displej a bzucak oznamuji jen vysledek (text, melodii)
        importlib.import_module(("." if balicek else "") + "_mp_knihovny", balicek or None).obal()
    else:
        sys.modules["microbit"]._reset()


def jmeno(deska=None):
    """Cele jmeno desky (pro vypis)."""
    return DESKY[deska or _rezim.deska]
