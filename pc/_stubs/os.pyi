"""
os – MicroPython práce se souborovým systémem (RP2040)

Tento soubor je STUB (typový popis) určený pro VS Code a Pylance.
Slouží pouze pro doplňování kódu a statickou analýzu. Neobsahuje
žádnou skutečnou implementaci.

MicroPython poskytuje základní funkce pro práci se souborovým
systémem na interním úložišti nebo na připojených médiích:

    - listdir(): výpis souborů a adresářů
    - remove(): smazání souboru
    - rename(): přejmenování souboru nebo adresáře
    - mkdir(), rmdir(): vytvoření a odstranění adresáře
    - stat(): informace o souboru
    - statvfs(): informace o souborovém systému

Používá se při práci s daty, logy, konfiguracemi nebo při ladění.
"""

from typing import List, Tuple


def listdir(path: str = "") -> List[str]:
    """
    Vrací seznam souborů a adresářů v dané cestě.

    Args:
        path: cesta k adresáři (prázdný řetězec = aktuální adresář).

    Returns:
        Seznam názvů souborů a adresářů.
    """
    ...


def remove(path: str) -> None:
    """
    Smaže soubor.

    Args:
        path: cesta k souboru.

    Poznámka:
        Pokud soubor neexistuje, vyvolá výjimku OSError.
    """
    ...


def rename(old: str, new: str) -> None:
    """
    Přejmenuje soubor nebo adresář.

    Args:
        old: původní název.
        new: nový název.
    """
    ...


def mkdir(path: str) -> None:
    """
    Vytvoří nový adresář.

    Args:
        path: cesta k adresáři.

    Poznámka:
        Pokud adresář již existuje, vyvolá OSError.
    """
    ...


def rmdir(path: str) -> None:
    """
    Odstraní prázdný adresář.

    Args:
        path: cesta k adresáři.

    Poznámka:
        Pokud adresář není prázdný, vyvolá OSError.
    """
    ...


def stat(path: str) -> Tuple[int, ...]:
    """
    Vrací informace o souboru nebo adresáři.

    Args:
        path: cesta k souboru nebo adresáři.

    Returns:
        N-tice obsahující metadata (velikost, typ, časové údaje…).
        Formát odpovídá MicroPython implementaci.
    """
    ...


def statvfs(path: str) -> Tuple[int, ...]:
    """
    Vrací informace o souborovém systému.

    Args:
        path: cesta k libovolnému souboru nebo adresáři.

    Returns:
        N-tice s informacemi o velikosti bloků, volném místě atd.
    """
    ...
