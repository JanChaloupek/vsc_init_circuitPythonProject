# _fake/_rezim.py

"""
Režim falešného hardwaru: test (výchozí) nebo simulace.

Stejné falešné moduly (board, digitalio, picoed, ...) slouží dvěma účelům:

- "test"  – unit testy (cpy test). Čas sám neběží, test ho posouvá ručně
            (adafruit_ticks.advance_ticks), nic se nevypisuje a test na konci
            kontroluje uložený stav (např. led.state_history).
- "sim"   – simulace programu na PC (cpy sim). Čas běží skutečně
            (time.sleep(1) opravdu čeká) a změny hardwaru se oznamují
            posluchačům - konzole simulace je vypisuje.

Falešné moduly samy nic nevypisují, jen při změně zavolají oznam().
V testu nikdo neposlouchá, takže se nic neděje.
"""

import time as _time    # skutečný modul time (načítá se dřív než falešný)

REZIM = "test"
_start = _time.monotonic()
_posluchaci = []


def nastav(rezim: str) -> None:
    """Přepne režim ("test" nebo "sim") a vynuluje počátek času."""
    global REZIM, _start
    if rezim not in ("test", "sim"):
        raise ValueError(f"Neznámý režim: {rezim}")
    REZIM = rezim
    _start = _time.monotonic()


def je_simulace() -> bool:
    return REZIM == "sim"


def realny_cas_ms() -> int:
    """Milisekundy od začátku simulace (podle skutečných hodin)."""
    return int((_time.monotonic() - _start) * 1000)


def realne_cekej(sekundy: float) -> None:
    """Skutečné čekání (jen v simulaci)."""
    if sekundy > 0:
        _time.sleep(sekundy)


def poslouchej(funkce) -> None:
    """Zaregistruje posluchače: funkce(co, kdo, hodnota)."""
    _posluchaci.append(funkce)


def prestan_poslouchat(funkce) -> None:
    if funkce in _posluchaci:
        _posluchaci.remove(funkce)


def oznam(co: str, kdo, hodnota=None) -> None:
    """Oznámí změnu hardwaru všem posluchačům.

    co      – druh zařízení: "pin", "displej", "bzucak", "tlacitko", "neopixel"
    kdo     – které zařízení (jméno pinu, "button_a", ...)
    hodnota – nová hodnota / stav
    """
    for funkce in list(_posluchaci):
        funkce(co, kdo, hodnota)
