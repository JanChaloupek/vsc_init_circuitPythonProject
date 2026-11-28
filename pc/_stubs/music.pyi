"""
music – melodie a tóny na BBC micro:bitu (MicroPython)

Tento soubor je STUB (typový popis) určený pro VS Code a Pylance.
Neobsahuje žádnou skutečnou implementaci (simulace na PC je
v pc/_fake/microbit_music.py).

Nota se zapisuje jako "JMÉNO[#|b][OKTÁVA][:DÉLKA]":

    "c4:4"   tón c ve 4. oktávě, délka 4 doby
    "eb:8"   es (e snížené), délka 8 dob
    "f#"     fis - oktáva a délka zůstávají z předchozí noty
    "r:2"    pauza 2 doby

Výchozí tempo je 4 doby na čtvrťovou notu a 120 čtvrťových not za minutu,
jedna doba tedy trvá 125 ms.

Typické použití:

    import music

    music.play(music.NYAN)
    music.play(["c4:4", "e", "g", "c5:8"])
    music.pitch(440, 500)
"""

from typing import Any, Sequence, Tuple, Union

_Melodie = Union[str, Sequence[str]]

DADADADUM: Tuple[str, ...]
"""Úvod 5. symfonie (Beethoven)."""
ENTERTAINER: Tuple[str, ...]
"""Úvod The Entertainer (Scott Joplin)."""
PRELUDE: Tuple[str, ...]
"""Preludium C dur (J. S. Bach)."""
ODE: Tuple[str, ...]
"""Óda na radost (Beethoven)."""
NYAN: Tuple[str, ...]
"""Nyan Cat."""
RINGTONE: Tuple[str, ...]
"""Vyzvánění telefonu."""
FUNK: Tuple[str, ...]
"""Funková basová linka."""
BLUES: Tuple[str, ...]
"""Blues."""
BIRTHDAY: Tuple[str, ...]
"""Happy Birthday."""
WEDDING: Tuple[str, ...]
"""Svatební pochod."""
FUNERAL: Tuple[str, ...]
"""Smuteční pochod."""
PUNCHLINE: Tuple[str, ...]
"""Pointa vtipu."""
PYTHON: Tuple[str, ...]
"""Znělka Monty Pythonů."""
BADDY: Tuple[str, ...]
"""Příchod padoucha."""
CHASE: Tuple[str, ...]
"""Honička."""
BA_DING: Tuple[str, ...]
"""Krátké upozornění."""
WAWAWAWAA: Tuple[str, ...]
"""Smutný trombon."""
JUMP_UP: Tuple[str, ...]
"""Skok nahoru (ve hře)."""
JUMP_DOWN: Tuple[str, ...]
"""Skok dolů (ve hře)."""
POWER_UP: Tuple[str, ...]
"""Získání bonusu (ve hře)."""
POWER_DOWN: Tuple[str, ...]
"""Ztráta bonusu (ve hře)."""


def play(music: _Melodie, pin: Any = ..., wait: bool = True, loop: bool = False) -> None:
    """
    Zahraje melodii.

    Args:
        music: vestavěná melodie (music.NYAN), seznam not nebo jedna nota ("c4:4").
        pin: kam se zvuk pošle (výchozí pin0 a na v2 i reproduktor).
        wait: True = počká, až melodie dohraje; False = hraje na pozadí.
        loop: True = hraje pořád dokola.
    """
    ...


def pitch(frequency: int, duration: int = -1, pin: Any = ..., wait: bool = True) -> None:
    """
    Zahraje tón.

    Args:
        frequency: výška tónu v Hz (440 = komorní a).
        duration: délka v ms; -1 = hraje, dokud ho nezastaví stop().
        wait: True = počká, až tón dozní.
    """
    ...


def stop(pin: Any = ...) -> None:
    """Zastaví melodii nebo tón."""
    ...


def set_tempo(ticks: int = 4, bpm: int = 120) -> None:
    """
    Nastaví tempo.

    Args:
        ticks: kolik dob má čtvrťová nota.
        bpm: kolik čtvrťových not zazní za minutu.
    """
    ...


def get_tempo() -> Tuple[int, int]:
    """Vrací tempo jako (ticks, bpm)."""
    ...


def reset() -> None:
    """Vrátí výchozí tempo (4, 120), oktávu 4 a délku noty 4."""
    ...
