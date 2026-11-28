"""
time – čas a čekání (CircuitPython i MicroPython)

Tento soubor je STUB (typový popis) určený pro VS Code a Pylance.
Slouží pouze pro doplňování kódu a statickou analýzu. Neobsahuje
žádnou skutečnou implementaci (simulace na PC je v pc/_fake).

Modul time je na obou platformách, ale funkce se liší. U každé
funkce je uvedeno, kde je:

    funkce                    CircuitPython   MicroPython   micro:bit
    sleep(s)                  ano             ano           ano
    monotonic(), monotonic_ns ano             -             -
    sleep_ms, sleep_us        -               ano           ano
    ticks_ms, ticks_us,
    ticks_add, ticks_diff     -               ano           ano
    time(), localtime(),
    mktime()                  ano             ano           -

V CircuitPythonu se intervaly měří pomocí monotonic() (sekundy jako
desetinné číslo) nebo knihovnou adafruit_ticks. V MicroPythonu pomocí
ticks_ms() a ticks_diff() - ticks po čase přetečou, proto se rozdíl
počítá vždy přes ticks_diff().
"""

from typing import Optional, Tuple


class struct_time(Tuple[int, int, int, int, int, int, int, int, int]):
    """
    Datum a čas (CircuitPython): tm_year, tm_mon, tm_mday, tm_hour, tm_min,
    tm_sec, tm_wday, tm_yday, tm_isdst. V MicroPythonu vrací localtime()
    obyčejnou osmici (rok, měsíc, den, hodina, minuta, sekunda, den v týdnu, den v roce).
    """

    tm_year: int
    tm_mon: int
    tm_mday: int
    tm_hour: int
    tm_min: int
    tm_sec: int
    tm_wday: int
    tm_yday: int
    tm_isdst: int


# =========================================================
# Obě platformy
# =========================================================

def sleep(seconds: float) -> None:
    """
    Pozastaví běh programu na daný počet sekund.

    Platforma: CircuitPython i MicroPython (i micro:bit).

    Args:
        seconds: počet sekund (může být desetinné číslo: 0.5 = půl sekundy).
    """
    ...


def time() -> int:
    """
    Vrací počet sekund od začátku epochy (podle hodin reálného času desky).

    Platforma: CircuitPython a MicroPython; na micro:bitu není.
    Bez nastavených hodin začíná čas při zapnutí desky - na měření
    intervalů použijte monotonic() (CircuitPython) nebo ticks_ms() (MicroPython).
    """
    ...


def localtime(secs: Optional[int] = None) -> struct_time:
    """
    Převede sekundy (výchozí: teď) na datum a čas.

    Platforma: CircuitPython a MicroPython; na micro:bitu není.
    """
    ...


def gmtime(secs: Optional[int] = None) -> struct_time:
    """
    Jako localtime(), ale v čase UTC (bez časového pásma).

    Platforma: jen MicroPython (Pico); na micro:bitu není.
    """
    ...


def mktime(t: Tuple[int, ...]) -> int:
    """
    Převede datum a čas (jako z localtime) zpět na sekundy.

    Platforma: CircuitPython a MicroPython; na micro:bitu není.
    """
    ...


def time_ns() -> int:
    """
    Vrací počet nanosekund od začátku epochy.

    Platforma: CircuitPython a MicroPython (novější verze); na micro:bitu není.
    """
    ...


# =========================================================
# Jen CircuitPython
# =========================================================

def monotonic() -> float:
    """
    Vrací čas v sekundách od zapnutí desky (desetinné číslo, nikdy neklesá).

    Platforma: jen CircuitPython (v MicroPythonu: ticks_ms()).

    Pozor: po několika hodinách běhu klesá přesnost (float) - na přesné
    intervaly použijte monotonic_ns() nebo knihovnu adafruit_ticks.

    Použití:
        start = time.monotonic()
        ...
        uplynulo = time.monotonic() - start
    """
    ...


def monotonic_ns() -> int:
    """
    Vrací čas v nanosekundách od zapnutí desky (celé číslo, přesné).

    Platforma: jen CircuitPython.
    """
    ...


# =========================================================
# Jen MicroPython
# =========================================================

def sleep_ms(ms: int) -> None:
    """
    Pozastaví běh programu na daný počet milisekund.

    Platforma: jen MicroPython (i micro:bit). V CircuitPythonu: time.sleep(ms / 1000).

    Args:
        ms: počet milisekund.
    """
    ...


def sleep_us(us: int) -> None:
    """
    Pozastaví běh programu na daný počet mikrosekund.

    Platforma: jen MicroPython (i micro:bit).

    Args:
        us: počet mikrosekund.
    """
    ...


def ticks_ms() -> int:
    """
    Vrací čas v milisekundách (počítadlo, které po čase přeteče).

    Platforma: jen MicroPython (i micro:bit). V CircuitPythonu:
    time.monotonic() nebo adafruit_ticks.ticks_ms().

    Rozdíl dvou časů počítejte vždy přes ticks_diff(), ne odečtením.
    """
    ...


def ticks_us() -> int:
    """
    Vrací čas v mikrosekundách (počítadlo, které po čase přeteče).

    Platforma: jen MicroPython (i micro:bit).
    """
    ...


def ticks_cpu() -> int:
    """
    Nejjemnější počítadlo, které deska má (jednotka podle desky).

    Platforma: jen MicroPython.
    """
    ...


def ticks_add(ticks: int, delta: int) -> int:
    """
    Přičte k času z ticks_ms() / ticks_us() hodnotu delta (správně i při přetečení).

    Platforma: jen MicroPython (i micro:bit).

    Použití:
        termin = ticks_add(ticks_ms(), 500)     # za 500 ms
    """
    ...


def ticks_diff(a: int, b: int) -> int:
    """
    Vrací rozdíl a - b dvou časů z ticks_ms() / ticks_us() (správně i při přetečení).

    Platforma: jen MicroPython (i micro:bit).

    Args:
        a: pozdější čas.
        b: dřívější čas.

    Použití:
        start = ticks_ms()
        ...
        uplynulo = ticks_diff(ticks_ms(), start)
    """
    ...
