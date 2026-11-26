"""
ujson – rychlá JSON knihovna pro MicroPython

Tento soubor je STUB (typový popis) určený pro VS Code a Pylance.
Slouží pouze pro doplňování kódu a statickou analýzu. Neobsahuje
žádnou skutečnou implementaci.

Modul ujson poskytuje základní funkce pro práci s JSON formátem:

    - loads(): převod JSON řetězce na Python objekt
    - dumps(): převod Python objektu na JSON řetězec

Používá se pro ukládání konfigurací, komunikaci s API nebo
přenos dat mezi zařízeními.
"""

from typing import Any


def loads(s: str) -> Any:
    """
    Načte JSON řetězec a převede jej na Python objekt.

    Args:
        s: JSON text.

    Returns:
        Python objekt (dict, list, int, float, bool nebo None).

    Raises:
        ValueError: pokud řetězec není validní JSON.
    """
    ...


def dumps(obj: Any) -> str:
    """
    Převede Python objekt na JSON řetězec.

    Args:
        obj: libovolný serializovatelný objekt.

    Returns:
        JSON text reprezentující daný objekt.

    Poznámka:
        Funkce neumožňuje pokročilé formátování (odsazení apod.).
    """
    ...
