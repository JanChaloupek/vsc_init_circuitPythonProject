"""
machine – MicroPython API pro hardware RP2040 (pico:ed)

Tento soubor je STUB (typový popis) určený pro VS Code a Pylance.
Slouží pouze pro doplňování kódu a statickou analýzu. Neobsahuje
žádnou skutečnou implementaci.

MicroPython na RP2040 poskytuje modul `machine`, který zpřístupňuje
nízkoúrovňové funkce mikrokontroleru:

    - Pin: digitální vstupy/výstupy
    - I2C / SoftI2C: komunikace po sběrnici I2C
    - SPI / SoftSPI: komunikace po sběrnici SPI
    - PWM: řízení výkonu pomocí pulzně šířkové modulace
    - UART: sériová komunikace
    - Timer: hardwarové časovače (běží v ISR)
    - ADC: analogově-digitální převodník
    - reset(), freq(): systémové funkce
    - mem32/mem16/mem8: přímý přístup do paměti

CircuitPython tento modul NEOBSAHUJE, proto je nutné mít vlastní
stubs, aby projekt na pico:ed fungoval správně ve VS Code.
"""

from typing import Any, Callable, Optional, Union


class Pin:
    """
    Pin – digitální vstup nebo výstup.

    Používá se pro ovládání LED, čtení tlačítek, řízení motorů
    a další základní práci s GPIO.

    Konstanty:
        IN: vstupní režim
        OUT: výstupní režim
        PULL_UP: aktivní interní pull-up rezistor
        PULL_DOWN: aktivní interní pull-down rezistor
    """

    IN: int
    OUT: int
    PULL_UP: int
    PULL_DOWN: int

    def __init__(self, id: Union[int, str], mode: int = None, pull: int = None) -> None:
        """
        Inicializuje pin.

        Args:
            id: číslo pinu nebo jeho název.
            mode: Pin.IN nebo Pin.OUT.
            pull: Pin.PULL_UP nebo Pin.PULL_DOWN.
        """
        ...

    def value(self, x: Optional[int] = None) -> int:
        """
        Čte nebo nastavuje hodnotu pinu.

        Args:
            x: pokud je None → čte hodnotu,
               pokud je 0/1 → nastaví hodnotu.

        Returns:
            Aktuální logická hodnota pinu (0 nebo 1).
        """
        ...

    def on(self) -> None:
        """Nastaví pin na logickou 1."""
        ...

    def off(self) -> None:
        """Nastaví pin na logickou 0."""
        ...


class I2C:
    """
    I2C – hardwarová komunikace po sběrnici I2C.

    Používá se pro senzory, displeje, expandéry a další periferie.
    """

    def __init__(self, id: int, *, scl: Pin, sda: Pin, freq: int = 400_000) -> None:
        """
        Inicializuje I2C sběrnici.

        Args:
            id: číslo I2C kontroléru (0 nebo 1).
            scl: pin hodin.
            sda: pin dat.
            freq: frekvence sběrnice v Hz.
        """
        ...

    def readfrom(self, addr: int, nbytes: int, stop: bool = True) -> bytes:
        """Čte data ze zařízení na adrese `addr`."""
        ...

    def writeto(self, addr: int, buf: bytes, stop: bool = True) -> int:
        """Zapíše data do zařízení na adrese `addr`."""
        ...

    def readfrom_mem(self, addr: int, memaddr: int, nbytes: int, *, addrsize: int = 8) -> bytes:
        """Čte z paměťového registru zařízení."""
        ...

    def writeto_mem(self, addr: int, memaddr: int, buf: bytes, *, addrsize: int = 8) -> int:
        """Zapisuje do paměťového registru zařízení."""
        ...


class SoftI2C(I2C):
    """Softwarová implementace I2C (pomalejší, ale flexibilní)."""
    ...


class SPI:
    """
    SPI – rychlá sériová komunikace.

    Používá se pro displeje, paměti, převodníky a další rychlé periferie.
    """

    def __init__(self, id: int, *, baudrate: int = 1_000_000, polarity: int = 0, phase: int = 0,
                 sck: Pin = None, mosi: Pin = None, miso: Pin = None) -> None:
        """
        Inicializuje SPI sběrnici.

        Args:
            id: číslo SPI kontroléru.
            baudrate: rychlost komunikace.
            polarity: polarita hodin.
            phase: fáze hodin.
            sck, mosi, miso: použité piny.
        """
        ...

    def read(self, nbytes: int) -> bytes:
        """Čte data ze SPI."""
        ...

    def write(self, buf: bytes) -> int:
        """Zapisuje data na SPI."""
        ...

    def write_readinto(self, wbuf: bytes, rbuf: bytearray) -> None:
        """Současně zapisuje a čte data."""
        ...


class SoftSPI(SPI):
    """Softwarová implementace SPI (pomalejší, ale flexibilní)."""
    ...


class PWM:
    """
    PWM – pulzně šířková modulace.

    Používá se pro řízení jasu LED, rychlosti motorů a serv.
    """

    def __init__(self, pin: Pin) -> None:
        """Inicializuje PWM na daném pinu."""
        ...

    def freq(self, f: Optional[int] = None) -> int:
        """
        Čte nebo nastavuje frekvenci PWM.

        Args:
            f: nová frekvence v Hz, nebo None pro čtení.

        Returns:
            Aktuální frekvence.
        """
        ...

    def duty_u16(self, v: Optional[int] = None) -> int:
        """
        Čte nebo nastavuje šířku pulzu (0–65535).

        Args:
            v: nová hodnota, nebo None pro čtení.

        Returns:
            Aktuální hodnota.
        """
        ...


class UART:
    """
    UART – sériová komunikace.

    Používá se pro GPS moduly, Bluetooth moduly, debug výstup atd.
    """

    def __init__(self, id: int, baudrate: int = 9600, bits: int = 8, parity: int = None,
                 stop: int = 1, tx: Pin = None, rx: Pin = None) -> None:
        """Inicializuje UART rozhraní."""
        ...

    def read(self, nbytes: int = None) -> Optional[bytes]:
        """Čte data z UARTu."""
        ...

    def write(self, buf: bytes) -> int:
        """Zapisuje data na UART."""
        ...


class Timer:
    """
    Timer – hardwarový časovač.

    Používá se pro periodické úlohy, animace, měření času atd.
    """

    ONE_SHOT: int
    PERIODIC: int

    def __init__(self, id: int = None) -> None:
        """Inicializuje časovač."""
        ...

    def init(self, *, period: int, mode: int, callback: Callable[[Any], None]) -> None:
        """
        Spustí časovač.

        Args:
            period: perioda v milisekundách.
            mode: Timer.ONE_SHOT nebo Timer.PERIODIC.
            callback: funkce volaná při každém přerušení.
        """
        ...

    def deinit(self) -> None:
        """Zastaví časovač."""
        ...


class ADC:
    """
    ADC – analogově-digitální převodník.

    Používá se pro čtení senzorů (světlo, potenciometr, napětí).
    """

    def __init__(self, pin: Union[int, Pin]) -> None:
        """Inicializuje ADC na daném pinu."""
        ...

    def read_u16(self) -> int:
        """Vrací 16bitovou hodnotu ADC (0–65535)."""
        ...


def reset() -> None:
    """Restartuje mikrokontroler."""
    ...


def freq() -> int:
    """Vrací frekvenci CPU v Hz."""
    ...


mem32: Any
mem16: Any
mem8: Any
