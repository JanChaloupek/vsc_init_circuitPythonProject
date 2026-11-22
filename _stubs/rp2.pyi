"""
rp2 – MicroPython funkce specifické pro RP2040 (PIO, stavové stroje)

Tento soubor je STUB (typový popis) určený pro VS Code a Pylance.
Slouží pouze pro doplňování kódu a statickou analýzu. Neobsahuje
žádnou skutečnou implementaci.

Modul rp2 zpřístupňuje unikátní hardware čipu RP2040:

    - PIO (Programmable I/O): programovatelné periférie
    - StateMachine: hardwarové stavové stroje
    - asm_pio: dekorátor pro definici PIO programů
    - const(): optimalizace konstant

PIO umožňuje vytvářet vlastní protokoly, řídit LED pásky,
generovat signály nebo zpracovávat data bez zatížení CPU.
"""

from typing import Any, Callable


def asm_pio(*, sideset_init=None, out_init=None, set_init=None,
            in_shiftdir=None, out_shiftdir=None, autopush=False,
            autopull=False, fifo_join=None) -> Callable:
    """
    Dekorátor pro definici PIO programu.

    Používá se k označení funkce obsahující PIO instrukce, které
    budou přeloženy do binární podoby a nahrány do PIO jednotky.

    Args:
        sideset_init: výchozí hodnota sideset pinů.
        out_init: výchozí hodnota OUT pinů.
        set_init: výchozí hodnota SET pinů.
        in_shiftdir: směr posunu IN shift registru.
        out_shiftdir: směr posunu OUT shift registru.
        autopush: automatické odesílání dat do FIFO.
        autopull: automatické načítání dat z FIFO.
        fifo_join: spojení TX/RX FIFO.

    Returns:
        Funkci reprezentující PIO program.
    """
    ...


def const(x: int) -> int:
    """
    Označí hodnotu jako konstantu pro optimalizaci.

    Args:
        x: hodnota konstanty.

    Returns:
        Stejná hodnota, ale označená pro optimalizaci překladačem.
    """
    ...


class StateMachine:
    """
    StateMachine – hardwarový stavový stroj PIO.

    Každý RP2040 má 8 stavových strojů (4 v každé PIO jednotce).
    Stavový stroj provádí PIO program nezávisle na CPU.

    Použití:
        sm = StateMachine(0, program, freq=2_000_000)
        sm.active(True)
        sm.put(123)
        value = sm.get()
    """

    def __init__(
        self, id: int, program: Callable, *, freq: int = 2000_000,
        sideset_base=None, out_base=None, set_base=None, in_base=None,
        jmp_pin=None
    ) -> None:
        """
        Inicializuje stavový stroj.

        Args:
            id: číslo stavového stroje (0–7).
            program: PIO program vytvořený pomocí @asm_pio.
            freq: frekvence vykonávání instrukcí.
            sideset_base: základní pin pro sideset.
            out_base: základní pin pro OUT instrukce.
            set_base: základní pin pro SET instrukce.
            in_base: základní pin pro IN instrukce.
            jmp_pin: pin použitý pro podmíněné skoky.
        """
        ...

    def active(self, value: bool = None) -> bool:
        """
        Aktivuje nebo deaktivuje stavový stroj.

        Args:
            value: True = spustit, False = zastavit, None = pouze zjistit stav.

        Returns:
            True pokud je stroj aktivní, jinak False.
        """
        ...

    def put(self, value: int) -> None:
        """
        Zapíše hodnotu do TX FIFO stavového stroje.

        Args:
            value: 32bitová hodnota.
        """
        ...

    def get(self) -> int:
        """
        Čte hodnotu z RX FIFO stavového stroje.

        Returns:
            32bitová hodnota načtená z FIFO.
        """
        ...

    def exec(self, instr: int) -> None:
        """
        Provede jednu PIO instrukci.

        Args:
            instr: binární kód instrukce.
        """
        ...
