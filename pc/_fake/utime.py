# _fake/utime.py

"""
Falešný modul time pro MicroPython (mpy sim, mpy test).

V MicroPythonu má time jiné funkce než v CircuitPythonu: sleep_ms,
sleep_us, ticks_ms, ticks_us, ticks_add, ticks_diff, ... Při běhu na PC
pro MicroPython se tento modul načte jako `time` i jako `utime`.

Čas je společný s ostatními falešnými moduly (adafruit_ticks):
- test: čas sám neběží, sleep_ms / sleep_us ho jen posunou
- sim:  čas běží podle skutečných hodin a sleep opravdu čeká

Funkce, které tu nejsou (monotonic, localtime, ...), se berou ze skutečného
modulu time - potřebuje je i standardní knihovna Pythonu (asyncio, threading).
"""

import time as _real

try:
    from . import _rezim                        # nacteno jako balicek _fake
    from . import adafruit_ticks as _ticks
except ImportError:
    import _rezim                               # nacteno primo ze slozky _fake
    import adafruit_ticks as _ticks

# Ticks maji stejnou periodu jako adafruit_ticks, aby ticks_diff fungoval
# pro milisekundy i mikrosekundy.
_PERIODA = _ticks._TICKS_PERIOD

# Test: zbytek mikrosekund, ktery jeste nedal celou milisekundu
_zbytek_us = 0


def _reset():
    global _zbytek_us
    _zbytek_us = 0


_rezim.pri_resetu(_reset)


# ---------------------------------------------------------
# Ticks
# ---------------------------------------------------------

ticks_ms = _ticks.ticks_ms
ticks_add = _ticks.ticks_add
ticks_diff = _ticks.ticks_diff


def ticks_us() -> int:
    """Mikrosekundy (pocitadlo, ktere po case pretece - pouzivej ticks_diff)."""
    if _rezim.je_simulace():
        return (_rezim.realny_cas_us() + _ticks._sim_offset * 1000) % _PERIODA
    return (_ticks._fake_ticks * 1000 + _zbytek_us) % _PERIODA


ticks_cpu = ticks_us


# ---------------------------------------------------------
# Cekani
# ---------------------------------------------------------

def sleep_us(us) -> None:
    """Pocka us mikrosekund (v testu jen posune cas)."""
    global _zbytek_us
    us = int(us)
    if us <= 0:
        return
    if _rezim.je_simulace():
        _rezim.realne_cekej(us / 1_000_000)
        return
    ms, _zbytek_us = divmod(_zbytek_us + us, 1000)
    if ms:
        _ticks.advance_ticks(ms)


def sleep_ms(ms) -> None:
    """Pocka ms milisekund (v testu jen posune cas)."""
    sleep_us(int(ms) * 1000)


def sleep(sekundy) -> None:
    """Pocka zadany pocet sekund (muze byt i desetinne cislo)."""
    sleep_us(round(sekundy * 1_000_000))


# ---------------------------------------------------------
# Datum a cas (skutecne hodiny PC)
# ---------------------------------------------------------

def time() -> int:
    """Sekundy od roku 1970 (cele cislo, jako v MicroPythonu)."""
    return int(_real.time())


time_ns = _real.time_ns
localtime = _real.localtime
gmtime = _real.gmtime
mktime = _real.mktime

# Pro standardni knihovnu Pythonu (unittest, asyncio, threading)
monotonic = _real.monotonic
perf_counter = _real.perf_counter


def __getattr__(jmeno):
    return getattr(_real, jmeno)
