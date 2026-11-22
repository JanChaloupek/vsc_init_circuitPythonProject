"""
time – MicroPython časové funkce (RP2040)

Tento soubor je STUB (typový popis) určený pro VS Code a Pylance.
Slouží pouze pro doplňování kódu a statickou analýzu. Neobsahuje
žádnou skutečnou implementaci.

MicroPython poskytuje základní funkce pro uspávání programu a
měření času:

    - sleep(), sleep_ms(), sleep_us(): zpoždění programu
    - ticks_ms(), ticks_us(): monotónní časovače
    - ticks_add(), ticks_diff(): bezpečné počítání s přetečením

Funkce ticks_* jsou monotónní (nikdy se nevrací zpět) a používají
se pro přesné měření časů a intervalů.
"""


def sleep(seconds: float) -> None:
    """
    Pozastaví běh programu na daný počet sekund.

    Args:
        seconds: počet sekund (může být desetinné číslo).
    """
    ...


def sleep_ms(ms: int) -> None:
    """
    Pozastaví běh programu na daný počet milisekund.

    Args:
        ms: počet milisekund.
    """
    ...


def sleep_us(us: int) -> None:
    """
    Pozastaví běh programu na daný počet mikrosekund.

    Args:
        us: počet mikrosekund.
    """
    ...


def ticks_ms() -> int:
    """
    Vrací monotónní čas v milisekundách.

    Returns:
        Hodnota časovače, která se postupně zvyšuje a po čase přeteče.
    """
    ...


def ticks_us() -> int:
    """
    Vrací monotónní čas v mikrosekundách.

    Returns:
        Hodnota časovače, která se postupně zvyšuje a po čase přeteče.
    """
    ...


def ticks_add(ticks: int, delta: int) -> int:
    """
    Bezpečně přičte hodnotu k časovači.

    Args:
        ticks: výchozí hodnota časovače.
        delta: počet milisekund nebo mikrosekund k přičtení.

    Returns:
        Nová hodnota časovače, správně ošetřená proti přetečení.
    """
    ...


def ticks_diff(a: int, b: int) -> int:
    """
    Vrací rozdíl dvou hodnot monotónního časovače.

    Args:
        a: pozdější čas.
        b: dřívější čas.

    Returns:
        Rozdíl v jednotkách časovače (ms nebo µs), bezpečně i při přetečení.

    Použití:
        start = ticks_ms()
        ...
        delta = ticks_diff(ticks_ms(), start)
    """
    ...
