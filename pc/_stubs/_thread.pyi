"""
_thread – MicroPython vlákna pro RP2040

Tento soubor je STUB (typový popis) určený pro VS Code a Pylance.
Slouží pouze pro doplňování kódu a statickou analýzu. Neobsahuje
žádnou skutečnou implementaci.

MicroPython na RP2040 umožňuje spouštět kód na druhém jádru CPU.
Modul _thread poskytuje jednoduché API pro práci s vlákny:

    - start_new_thread(): spustí funkci na druhém jádru
    - allocate_lock(): vytvoří jednoduchý zámek (mutex)
    - LockType: objekt zámku s metodami acquire() a release()

Vlákna v MicroPythonu jsou velmi jednoduchá a sdílejí stejnou paměť.
Používají se například pro paralelní vykreslování displeje nebo
zpracování senzorů na pozadí.
"""

from typing import Callable, Any


def start_new_thread(func: Callable, args: tuple) -> int:
    """
    Spustí nové vlákno na druhém jádru RP2040.

    Args:
        func: Funkce, která se má spustit ve vlákně.
        args: Argumenty předané funkci (musí být tuple).

    Returns:
        ID nového vlákna (číslo), nebo 0 při chybě.

    Poznámka:
        Vlákna sdílejí stejný paměťový prostor. Je nutné používat
        zámky, pokud více vláken pracuje se stejnými daty.
    """
    ...


class LockType:
    """
    Jednoduchý zámek (mutex) pro synchronizaci vláken.

    Metody:
        acquire(): pokusí se získat zámek
        release(): uvolní zámek
    """

    def acquire(self, blocking: bool = True) -> bool:
        """
        Pokusí se získat zámek.

        Args:
            blocking: Pokud je True, vlákno čeká, dokud není zámek volný.
                      Pokud je False, funkce se vrátí okamžitě.

        Returns:
            True pokud byl zámek získán, jinak False.
        """
        ...

    def release(self) -> None:
        """
        Uvolní zámek.

        Poznámka:
            Pokud zámek nevlastní aktuální vlákno, může dojít k chybě.
        """
        ...


def allocate_lock() -> LockType:
    """
    Vytvoří a vrátí nový zámek (mutex).

    Returns:
        Instance LockType.

    Použití:
        lock = allocate_lock()
        if lock.acquire():
            ... kritická sekce ...
            lock.release()
    """
    ...
