"""
sys – systémové funkce MicroPythonu (RP2040)

Tento soubor je STUB (typový popis) určený pro VS Code a Pylance.
Slouží pouze pro doplňování kódu a statickou analýzu. Neobsahuje
žádnou skutečnou implementaci.

MicroPython poskytuje zjednodušený modul sys, který obsahuje:

    - platform: název platformy (např. "rp2")
    - implementation: informace o MicroPythonu
    - exit(): ukončení programu
    - print_exception(): tisk tracebacku

Používá se hlavně pro ladění, diagnostiku a řízení běhu programu.
"""

platform: str
"""Název platformy, např. 'rp2' pro RP2040."""

implementation: tuple
"""Informace o implementaci MicroPythonu (verze, build…)."""


def exit(code: int = 0) -> None:
    """
    Ukončí běh programu.

    Args:
        code: návratový kód (výchozí 0).

    Poznámka:
        V MicroPythonu může exit() ukončit pouze aktuální skript,
        nikoli celý firmware.
    """
    ...


def print_exception(exc: BaseException) -> None:
    """
    Vytiskne traceback výjimky na sériový výstup.

    Args:
        exc: výjimka, která má být vypsána.

    Použití:
        try:
            ...
        except Exception as e:
            print_exception(e)
    """
    ...
