"""
random – MicroPython generátor náhodných čísel

Tento soubor je STUB (typový popis) určený pro VS Code a Pylance.
Slouží pouze pro doplňování kódu a statickou analýzu. Neobsahuje
žádnou skutečnou implementaci.

MicroPython poskytuje zjednodušený modul random, který umožňuje:

    - getrandbits(): získání náhodných bitů
    - randrange(): náhodné číslo z intervalu s krokem
    - randint(): náhodné celé číslo včetně obou hranic

Používá se pro hry, simulace, náhodné volby a jednoduché algoritmy.
"""


def getrandbits(n: int) -> int:
    """
    Vrací náhodné celé číslo o velikosti n bitů.

    Args:
        n: počet náhodných bitů.

    Returns:
        Náhodné číslo v rozsahu 0 až (2**n - 1).
    """
    ...


def randrange(start: int, stop: int = None, step: int = 1) -> int:
    """
    Vrací náhodné číslo z aritmetické posloupnosti.

    Args:
        start: začátek intervalu (včetně).
        stop: konec intervalu (exkluzivně). Pokud je None, bere se jako 0..start.
        step: krok mezi hodnotami.

    Returns:
        Náhodná hodnota z rozsahu start..stop se zadaným krokem.
    """
    ...


def randint(a: int, b: int) -> int:
    """
    Vrací náhodné celé číslo včetně obou hranic.

    Args:
        a: dolní mez (včetně).
        b: horní mez (včetně).

    Returns:
        Náhodné celé číslo mezi a a b.
    """
    ...
