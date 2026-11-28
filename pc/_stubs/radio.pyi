"""
radio – bezdrátové zprávy mezi BBC micro:bity (MicroPython)

Tento soubor je STUB (typový popis) určený pro VS Code a Pylance.
Neobsahuje žádnou skutečnou implementaci (simulace na PC je
v pc/_fake/microbit_radio.py).

Zprávy si vyměňují micro:bity se stejným kanálem (channel) a skupinou
(group). Rádio se musí nejdřív zapnout:

    import radio

    radio.on()
    radio.config(group=7)
    radio.send("ahoj")
    zprava = radio.receive()        # None, když nic nepřišlo
"""

from typing import Optional, Tuple, Union

RATE_1MBIT: int
"""Rychlost přenosu 1 Mbit/s (výchozí)."""
RATE_2MBIT: int
"""Rychlost přenosu 2 Mbit/s."""


def on() -> None:
    """Zapne rádio (bere proud a paměť - bez on() nejde nic poslat ani přijmout)."""
    ...


def off() -> None:
    """Vypne rádio."""
    ...


def config(
    *,
    length: int = 32,
    queue: int = 3,
    channel: int = 7,
    power: int = 6,
    address: int = 0x75626974,
    group: int = 0,
    data_rate: int = ...,
) -> None:
    """
    Nastaví rádio. Zadávají se jen hodnoty, které se mají změnit.

    Args:
        length: největší délka zprávy v bajtech (nejvýš 251).
        queue: kolik přijatých zpráv se pamatuje (další se zahodí).
        channel: kanál 0–83.
        power: vysílací výkon 0–7.
        address: 32bitová adresa.
        group: skupina 0–255 - zprávy dostanou jen micro:bity se stejnou skupinou.
        data_rate: radio.RATE_1MBIT nebo radio.RATE_2MBIT.
    """
    ...


def reset() -> None:
    """Vrátí výchozí nastavení."""
    ...


def send(message: str) -> None:
    """Pošle text."""
    ...


def receive() -> Optional[str]:
    """Vrací nejstarší přijatý text, None = nic nepřišlo."""
    ...


def send_bytes(message: Union[bytes, bytearray]) -> None:
    """Pošle bajty."""
    ...


def receive_bytes() -> Optional[bytes]:
    """Vrací nejstarší přijatou zprávu jako bajty, None = nic nepřišlo."""
    ...


def receive_full() -> Optional[Tuple[bytes, int, int]]:
    """Vrací (zpráva, síla signálu v dBm, čas příjmu v µs), None = nic nepřišlo."""
    ...
