# _fake/_rezim.py

"""
Režim falešného hardwaru: test (výchozí) nebo simulace.

Stejné falešné moduly (board, digitalio, picoed, machine, ...) slouží dvěma účelům:

- "test"  – unit testy (cpy test, mpy test). Čas sám neběží, test ho posouvá
            ručně (adafruit_ticks.advance_ticks, time.sleep), nic se nevypisuje
            a test na konci kontroluje uložený stav (např. led.state_history).
- "sim"   – simulace programu na PC (cpy sim, mpy sim). Čas běží skutečně
            (time.sleep(1) opravdu čeká) a změny hardwaru se oznamují
            posluchačům - konzole simulace je vypisuje.

Falešné moduly samy nic nevypisují, jen při změně zavolají oznam().
V testu nikdo neposlouchá, takže se nic neděje.

Další společné věci pro falešné moduly:
- tlačítka:  deska zaregistruje, co udělá stisk klávesy "a" / "b"
             (registruj_tlacitko), konzole pak volá stiskni()
- ticho():   během volání knihovny (např. rolování textu na displeji)
             se dílčí změny neoznamují - knihovna oznámí jen výsledek
- casovace:  falešný machine.Timer se v testu spouští posunem času
             (adafruit_ticks.advance_ticks volá casovace(cil_ms))
- resetuj(): před každým testem vrátí hardware do výchozího stavu
"""

import contextlib
import threading
import time as _time    # skutečný modul time (načítá se dřív než falešný)

REZIM = "test"
_start = _time.monotonic()
_posluchaci = []
_tlacitka = {}
_pri_resetu = []
_vlakno = threading.local()

# Funkce cil_ms -> None, kterou adafruit_ticks.advance_ticks v testu zavolá
# před posunem času (spustí časovače machine.Timer, které mezitím vyprší).
casovace = None


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


def realny_cas_us() -> int:
    """Mikrosekundy od začátku simulace (podle skutečných hodin)."""
    return int((_time.monotonic() - _start) * 1_000_000)


def realne_cekej(sekundy: float) -> None:
    """Skutečné čekání (jen v simulaci).

    Čeká po krátkých úsecích, aby šla simulace kdykoli ukončit
    (klávesa q / Ctrl+C se projeví nejpozději za 0,05 s)."""
    konec = _time.monotonic() + sekundy
    while True:
        zbyva = konec - _time.monotonic()
        if zbyva <= 0:
            return
        _time.sleep(min(zbyva, 0.05))


# ---------------------------------------------------------
# Oznamování změn
# ---------------------------------------------------------

def poslouchej(funkce) -> None:
    """Zaregistruje posluchače: funkce(co, kdo, hodnota)."""
    _posluchaci.append(funkce)


def prestan_poslouchat(funkce) -> None:
    if funkce in _posluchaci:
        _posluchaci.remove(funkce)


def oznam(co: str, kdo, hodnota=None) -> None:
    """Oznámí změnu hardwaru všem posluchačům.

    co      – druh zařízení: "pin", "pwm", "displej", "bzucak", "tlacitko", "neopixel"
    kdo     – které zařízení (jméno pinu, "BUTTON_A", ...)
    hodnota – nová hodnota / stav
    """
    if getattr(_vlakno, "ticho", 0):
        return
    for funkce in list(_posluchaci):
        funkce(co, kdo, hodnota)


@contextlib.contextmanager
def ticho():
    """Uvnitř bloku `with ticho():` se v tomto vlákně nic neoznamuje."""
    _vlakno.ticho = getattr(_vlakno, "ticho", 0) + 1
    try:
        yield
    finally:
        _vlakno.ticho -= 1


# ---------------------------------------------------------
# Tlačítka (klávesy konzole simulace)
# ---------------------------------------------------------

def registruj_tlacitko(klavesa: str, funkce) -> None:
    """Klávesa ("a", "b") -> funkce(stisknuto: bool), která tlačítko stiskne / pustí."""
    _tlacitka[klavesa] = funkce


def stiskni(klavesa: str, stisknuto: bool = True) -> bool:
    """Stiskne / pustí tlačítko klávesy. Vrátí False, když deska takové tlačítko nemá."""
    funkce = _tlacitka.get(klavesa)
    if funkce is None:
        return False
    funkce(stisknuto)
    return True


# ---------------------------------------------------------
# Reset před testem
# ---------------------------------------------------------

def pri_resetu(funkce) -> None:
    """Zaregistruje funkci, která vrátí část hardwaru do výchozího stavu."""
    if funkce not in _pri_resetu:
        _pri_resetu.append(funkce)


def resetuj() -> None:
    """Vrátí hardware do výchozího stavu (volá se před každým testem)."""
    for funkce in list(_pri_resetu):
        funkce()
