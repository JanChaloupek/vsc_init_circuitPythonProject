"""
ure – MicroPython regulární výrazy (zjednodušené regexy)

Tento soubor je STUB (typový popis) určený pro VS Code a Pylance.
Slouží pouze pro doplňování kódu a statickou analýzu. Neobsahuje
žádnou skutečnou implementaci.

Modul ure poskytuje zjednodušenou podporu regulárních výrazů:

    - compile(): vytvoří regex objekt
    - match(): hledá shodu na začátku textu
    - search(): hledá shodu kdekoliv v textu

MicroPython implementuje pouze základní subset Python regexů,
ale pro většinu jednoduchých úloh (parsování čísel, příkazů,
formátů) to bohatě stačí.
"""

from typing import Optional, Any


def compile(pattern: str) -> Any:
    """
    Přeloží regulární výraz a vrátí regex objekt.

    Args:
        pattern: regulární výraz ve formě řetězce.

    Returns:
        Objekt reprezentující zkompilovaný regex.

    Raises:
        ValueError: pokud je výraz neplatný.
    """
    ...


def match(pattern: str, text: str) -> Optional[Any]:
    """
    Pokusí se najít shodu na začátku textu.

    Args:
        pattern: regulární výraz.
        text: text, ve kterém se hledá.

    Returns:
        Match objekt při úspěchu, nebo None.
    """
    ...


def search(pattern: str, text: str) -> Optional[Any]:
    """
    Hledá první výskyt regulárního výrazu v textu.

    Args:
        pattern: regulární výraz.
        text: text, ve kterém se hledá.

    Returns:
        Match objekt při úspěchu, nebo None.
    """
    ...
