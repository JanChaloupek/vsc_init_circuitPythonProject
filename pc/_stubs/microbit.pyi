"""
microbit – MicroPython pro BBC micro:bit v2

Tento soubor je STUB (typový popis) určený pro VS Code a Pylance.
Slouží pouze pro doplňování kódu a statickou analýzu. Neobsahuje
žádnou skutečnou implementaci (simulace na PC je v pc/_fake/microbit.py).

Modul `microbit` zpřístupňuje hardware desky:

    - display: displej 5 × 5 LED s jasem 0–9
    - Image: obrázky pro displej (Image.HEART, Image("09090:..."))
    - button_a, button_b: tlačítka A a B
    - pin0 – pin20, pin_logo, pin_speaker: piny na hraně desky
    - i2c, spi, uart: sběrnice
    - accelerometer, compass, microphone: senzory
    - speaker, audio, Sound: zvuk (micro:bit v2)
    - sleep(ms), running_time(), temperature()

Pozor: sleep() bere MILISEKUNDY (sleep(500) = půl sekundy),
time.sleep() bere sekundy.

Typické použití:

    from microbit import *

    display.scroll("Ahoj")
    while True:
        if button_a.was_pressed():
            display.show(Image.HEART)
        sleep(100)
"""

from typing import Any, Iterable, List, Optional, Tuple, Union, overload

__all__ = [
    "display", "Image", "button_a", "button_b",
    "pin0", "pin1", "pin2", "pin3", "pin4", "pin5", "pin6", "pin7", "pin8", "pin9", "pin10",
    "pin11", "pin12", "pin13", "pin14", "pin15", "pin16", "pin19", "pin20", "pin_logo", "pin_speaker",
    "i2c", "uart", "spi", "accelerometer", "compass", "microphone", "speaker", "audio",
    "Sound", "SoundEvent", "sleep", "running_time", "temperature", "set_volume", "reset", "panic",
]


# =========================================================
# Funkce
# =========================================================

def sleep(ms: Union[int, float]) -> None:
    """
    Počká zadaný počet MILISEKUND.

    Args:
        ms: počet milisekund (sleep(1000) = 1 sekunda).
            Desetinná část se zahodí: sleep(0.5) nečeká vůbec.
    """
    ...


def running_time() -> int:
    """Vrací počet milisekund od zapnutí (nebo restartu) desky."""
    ...


def temperature() -> int:
    """Vrací teplotu procesoru ve stupních Celsia (přibližně teplota okolí)."""
    ...


def set_volume(value: int) -> None:
    """
    Nastaví hlasitost reproduktoru a výstupu zvuku.

    Args:
        value: 0 (ticho) až 255 (nejhlasitěji).
    """
    ...


def reset() -> None:
    """Restartuje desku (program začne znovu od začátku)."""
    ...


def panic(n: int = 0) -> None:
    """
    Zastaví program a na displeji ukazuje smutný obličej a číslo n.

    Args:
        n: kód chyby 0–255.
    """
    ...


# =========================================================
# Image
# =========================================================

class Image:
    """
    Obrázek z bodů s jasem 0 (nesvítí) až 9 (nejjasněji).

    Vytvoření:
        Image("09090:99999:99999:09990:00900")   řádky oddělené dvojtečkou
        Image(5, 5)                              prázdný obrázek 5 × 5
        Image(2, 2, bytearray([9, 0, 0, 9]))     z hodnot jasu

    Vestavěné obrázky (Image.HEART, Image.HAPPY, ...) nejdou měnit –
    nejdřív si je zkopírujte: img = Image.HEART.copy().
    """

    HEART: Image
    HEART_SMALL: Image
    HAPPY: Image
    SMILE: Image
    SAD: Image
    CONFUSED: Image
    ANGRY: Image
    ASLEEP: Image
    SURPRISED: Image
    SILLY: Image
    FABULOUS: Image
    MEH: Image
    YES: Image
    NO: Image
    CLOCK12: Image
    CLOCK1: Image
    CLOCK2: Image
    CLOCK3: Image
    CLOCK4: Image
    CLOCK5: Image
    CLOCK6: Image
    CLOCK7: Image
    CLOCK8: Image
    CLOCK9: Image
    CLOCK10: Image
    CLOCK11: Image
    ARROW_N: Image
    ARROW_NE: Image
    ARROW_E: Image
    ARROW_SE: Image
    ARROW_S: Image
    ARROW_SW: Image
    ARROW_W: Image
    ARROW_NW: Image
    TRIANGLE: Image
    TRIANGLE_LEFT: Image
    CHESSBOARD: Image
    DIAMOND: Image
    DIAMOND_SMALL: Image
    SQUARE: Image
    SQUARE_SMALL: Image
    RABBIT: Image
    COW: Image
    MUSIC_CROTCHET: Image
    MUSIC_QUAVER: Image
    MUSIC_QUAVERS: Image
    PITCHFORK: Image
    XMAS: Image
    PACMAN: Image
    TARGET: Image
    TSHIRT: Image
    ROLLERSKATE: Image
    DUCK: Image
    HOUSE: Image
    TORTOISE: Image
    BUTTERFLY: Image
    STICKFIGURE: Image
    GHOST: Image
    SWORD: Image
    GIRAFFE: Image
    SKULL: Image
    UMBRELLA: Image
    SNAKE: Image
    SCISSORS: Image

    ALL_CLOCKS: Tuple[Image, ...]
    """Ručičky hodin po hodinách (12, 1, 2, ... 11) – vhodné pro animaci."""
    ALL_ARROWS: Tuple[Image, ...]
    """Šipky po směru hodinových ručiček (N, NE, E, ... NW)."""

    @overload
    def __init__(self) -> None: ...
    @overload
    def __init__(self, string: str) -> None: ...
    @overload
    def __init__(self, width: int, height: int, buffer: Optional[Iterable[int]] = None) -> None: ...

    def width(self) -> int:
        """Šířka obrázku v bodech."""
        ...

    def height(self) -> int:
        """Výška obrázku v bodech."""
        ...

    def set_pixel(self, x: int, y: int, value: int) -> None:
        """
        Nastaví jas bodu.

        Args:
            x: sloupec (0 = vlevo).
            y: řádek (0 = nahoře).
            value: jas 0–9.
        """
        ...

    def get_pixel(self, x: int, y: int) -> int:
        """Vrací jas bodu (0–9)."""
        ...

    def fill(self, value: int) -> None:
        """Nastaví všem bodům jas value (0–9)."""
        ...

    def copy(self) -> Image:
        """Vrací kopii obrázku (tu jde měnit i u vestavěných obrázků)."""
        ...

    def crop(self, x: int, y: int, w: int, h: int) -> Image:
        """Vrací výřez obrázku: w × h bodů od bodu (x, y)."""
        ...

    def shift_left(self, n: int) -> Image:
        """Vrací obrázek posunutý o n sloupců doleva (zprava přibudou zhasnuté body)."""
        ...

    def shift_right(self, n: int) -> Image:
        """Vrací obrázek posunutý o n sloupců doprava."""
        ...

    def shift_up(self, n: int) -> Image:
        """Vrací obrázek posunutý o n řádků nahoru."""
        ...

    def shift_down(self, n: int) -> Image:
        """Vrací obrázek posunutý o n řádků dolů."""
        ...

    def invert(self) -> Image:
        """Vrací obrázek s obráceným jasem (9 - jas)."""
        ...

    def blit(self, src: Image, x: int, y: int, w: int, h: int, xdest: int = 0, ydest: int = 0) -> None:
        """Zkopíruje výřez w × h od (x, y) z obrázku src na pozici (xdest, ydest) tohoto obrázku."""
        ...

    def __add__(self, other: Image) -> Image:
        """Sečte jas bodů dvou stejně velkých obrázků (nejvýš 9)."""
        ...

    def __mul__(self, n: float) -> Image:
        """Vynásobí jas všech bodů číslem n (nejvýš 9)."""
        ...

    def __truediv__(self, n: float) -> Image:
        """Vydělí jas všech bodů číslem n."""
        ...


# =========================================================
# Displej
# =========================================================

class MicroBitDisplay:
    """Displej 5 × 5 LED. Bod (0, 0) je vlevo nahoře."""

    def show(
        self,
        image: Union[Image, str, int, float, Iterable[Union[Image, str]]],
        delay: int = 400,
        *,
        wait: bool = True,
        loop: bool = False,
        clear: bool = False,
    ) -> None:
        """
        Ukáže obrázek, číslo, text (znak po znaku) nebo animaci (seznam obrázků).

        Args:
            image: Image, číslo, text nebo seznam obrázků.
            delay: jak dlouho je vidět jeden znak / snímek (ms).
            wait: True = počká, až se všechno ukáže; False = běží na pozadí.
            loop: True = opakuje se pořád dokola.
            clear: True = na konci displej smaže.
        """
        ...

    def scroll(
        self,
        text: Union[str, int, float],
        delay: int = 150,
        *,
        wait: bool = True,
        loop: bool = False,
        monospace: bool = False,
    ) -> None:
        """
        Text projede displejem zprava doleva.

        Args:
            text: text nebo číslo.
            delay: rychlost – ms na posun o jeden sloupec (víc = pomaleji).
            wait: True = počká, až text dojede; False = běží na pozadí.
            loop: True = opakuje se pořád dokola.
            monospace: True = každé písmeno má 5 sloupců.
        """
        ...

    def clear(self) -> None:
        """Zhasne celý displej."""
        ...

    def set_pixel(self, x: int, y: int, value: int) -> None:
        """
        Rozsvítí bod.

        Args:
            x: sloupec 0–4 (0 = vlevo).
            y: řádek 0–4 (0 = nahoře).
            value: jas 0 (nesvítí) až 9.
        """
        ...

    def get_pixel(self, x: int, y: int) -> int:
        """Vrací jas bodu (0–9)."""
        ...

    def on(self) -> None:
        """Zapne displej."""
        ...

    def off(self) -> None:
        """Vypne displej (piny displeje jde pak použít k něčemu jinému)."""
        ...

    def is_on(self) -> bool:
        """True, když je displej zapnutý."""
        ...

    def read_light_level(self) -> int:
        """Vrací osvětlení naměřené LED displeje: 0 (tma) až 255 (světlo)."""
        ...


display: MicroBitDisplay
"""Displej 5 × 5 LED."""


# =========================================================
# Tlačítka
# =========================================================

class MicroBitButton:
    """Tlačítko na desce."""

    def is_pressed(self) -> bool:
        """True, dokud je tlačítko stisknuté."""
        ...

    def was_pressed(self) -> bool:
        """True, když bylo tlačítko od posledního volání stisknuto (stisk se tím „spotřebuje“)."""
        ...

    def get_presses(self) -> int:
        """Vrací počet stisků od posledního volání a počítadlo vynuluje."""
        ...


button_a: MicroBitButton
"""Tlačítko A (vlevo)."""
button_b: MicroBitButton
"""Tlačítko B (vpravo)."""


# =========================================================
# Piny
# =========================================================

class MicroBitDigitalPin:
    """Digitální pin. Umí i write_analog (PWM – např. jas LED, rychlost motoru)."""

    NO_PULL: int
    PULL_DOWN: int
    PULL_UP: int

    def write_digital(self, value: int) -> None:
        """Nastaví výstup: 1 = 3,3 V, 0 = 0 V."""
        ...

    def read_digital(self) -> int:
        """Přečte vstup: 1 = napětí, 0 = žádné napětí."""
        ...

    def set_pull(self, value: int) -> None:
        """Vnitřní rezistor vstupu: pin.PULL_UP, pin.PULL_DOWN (výchozí) nebo pin.NO_PULL."""
        ...

    def get_pull(self) -> int:
        """Vrací nastavení vnitřního rezistoru (PULL_UP, PULL_DOWN, NO_PULL)."""
        ...

    def get_mode(self) -> str:
        """Jak se pin naposledy použil: "unused", "write_digital", "read_digital", "write_analog", ..."""
        ...

    def write_analog(self, value: int) -> None:
        """
        PWM výstup: střída 0 (stále 0 V) až 1023 (stále 3,3 V).

        Args:
            value: 0–1023 (512 = polovinu času zapnuto).
        """
        ...

    def set_analog_period(self, period: int) -> None:
        """Perioda PWM v milisekundách (výchozí 20 ms)."""
        ...

    def set_analog_period_microseconds(self, period: int) -> None:
        """Perioda PWM v mikrosekundách (nejméně 256)."""
        ...

    def get_analog_period_microseconds(self) -> int:
        """Vrací periodu PWM v mikrosekundách."""
        ...


class MicroBitAnalogDigitalPin(MicroBitDigitalPin):
    """Pin s analogovým vstupem (pin0–pin4, pin10)."""

    def read_analog(self) -> int:
        """Napětí na pinu: 0 (0 V) až 1023 (3,3 V)."""
        ...


class MicroBitTouchPin(MicroBitAnalogDigitalPin):
    """Pin s analogovým vstupem a dotykem (pin0–pin2, velké ploché kontakty)."""

    RESISTIVE: int
    CAPACITIVE: int

    def is_touched(self) -> bool:
        """True, když se pinu někdo dotýká (druhou rukou držte GND)."""
        ...

    def set_touch_mode(self, value: int) -> None:
        """Druh dotyku: pin.RESISTIVE (výchozí u pin0–pin2) nebo pin.CAPACITIVE."""
        ...


class MicroBitTouchOnlyPin:
    """Dotykové logo na přední straně micro:bitu v2."""

    RESISTIVE: int
    CAPACITIVE: int

    def is_touched(self) -> bool:
        """True, když se někdo dotýká loga."""
        ...

    def set_touch_mode(self, value: int) -> None:
        """Druh dotyku: pin_logo.CAPACITIVE (výchozí) nebo pin_logo.RESISTIVE."""
        ...


pin0: MicroBitTouchPin
pin1: MicroBitTouchPin
pin2: MicroBitTouchPin
pin3: MicroBitAnalogDigitalPin
"""Sdílený s displejem (sloupec 1)."""
pin4: MicroBitAnalogDigitalPin
"""Sdílený s displejem (sloupec 2)."""
pin5: MicroBitDigitalPin
"""Tlačítko A (stisk = 0)."""
pin6: MicroBitDigitalPin
"""Sdílený s displejem."""
pin7: MicroBitDigitalPin
"""Sdílený s displejem."""
pin8: MicroBitDigitalPin
pin9: MicroBitDigitalPin
"""Sdílený s displejem."""
pin10: MicroBitAnalogDigitalPin
"""Sdílený s displejem (sloupec 3)."""
pin11: MicroBitDigitalPin
"""Tlačítko B (stisk = 0)."""
pin12: MicroBitDigitalPin
pin13: MicroBitDigitalPin
"""SPI SCK."""
pin14: MicroBitDigitalPin
"""SPI MISO."""
pin15: MicroBitDigitalPin
"""SPI MOSI."""
pin16: MicroBitDigitalPin
pin19: MicroBitDigitalPin
"""I2C SCL."""
pin20: MicroBitDigitalPin
"""I2C SDA."""
pin_logo: MicroBitTouchOnlyPin
"""Dotykové logo (micro:bit v2)."""
pin_speaker: MicroBitDigitalPin
"""Reproduktor na desce (micro:bit v2)."""


# =========================================================
# Sběrnice
# =========================================================

class MicroBitI2C:
    """Sběrnice I2C na pin19 (SCL) a pin20 (SDA) – senzory a řadiče robota."""

    def init(self, freq: int = 100000, sda: MicroBitDigitalPin = ..., scl: MicroBitDigitalPin = ...) -> None:
        """
        Nastaví sběrnici.

        Args:
            freq: rychlost v Hz (100000 nebo 400000).
            sda, scl: piny sběrnice (výchozí pin20, pin19).
        """
        ...

    def scan(self) -> List[int]:
        """Vrací adresy zařízení, která na sběrnici odpověděla."""
        ...

    def read(self, addr: int, n: int, repeat: bool = False) -> bytes:
        """
        Přečte n bajtů ze zařízení. Když na adrese nikdo není: OSError (ENODEV).

        Args:
            addr: 7bitová adresa zařízení (např. 0x38).
            n: počet bajtů.
            repeat: True = bez stop bitu (další přenos navazuje).
        """
        ...

    def write(self, addr: int, buf: Union[bytes, bytearray], repeat: bool = False) -> None:
        """
        Zapíše bajty do zařízení (u většiny zařízení je první bajt číslo registru).

        Args:
            addr: 7bitová adresa zařízení.
            buf: bajty k zápisu.
            repeat: True = bez stop bitu (např. před čtením registru).
        """
        ...


class MicroBitSPI:
    """Sběrnice SPI (výchozí piny pin13 SCK, pin15 MOSI, pin14 MISO)."""

    def init(
        self,
        baudrate: int = 1000000,
        bits: int = 8,
        mode: int = 0,
        sclk: MicroBitDigitalPin = ...,
        mosi: MicroBitDigitalPin = ...,
        miso: MicroBitDigitalPin = ...,
    ) -> None:
        """Nastaví rychlost, režim a piny sběrnice."""
        ...

    def write(self, buf: Union[bytes, bytearray]) -> None:
        """Pošle bajty."""
        ...

    def read(self, nbytes: int, write: int = 0) -> bytes:
        """Přečte nbytes bajtů (a přitom posílá bajt write)."""
        ...

    def write_readinto(self, out: Union[bytes, bytearray], in_: bytearray) -> None:
        """Pošle bajty z out a zároveň čte do in_ (stejná délka)."""
        ...


class MicroBitUART:
    """Sériová linka. Bez tx / rx jde přes USB do počítače (jako print)."""

    ODD: int
    EVEN: int

    def init(
        self,
        baudrate: int = 9600,
        bits: int = 8,
        parity: Optional[int] = None,
        stop: int = 1,
        *,
        tx: Optional[MicroBitDigitalPin] = None,
        rx: Optional[MicroBitDigitalPin] = None,
    ) -> None:
        """Nastaví linku. S piny tx / rx přestane fungovat REPL přes USB."""
        ...

    def any(self) -> bool:
        """True, když čekají přijatá data."""
        ...

    def read(self, nbytes: Optional[int] = None) -> Optional[bytes]:
        """Přečte až nbytes bajtů (None = nic nepřišlo)."""
        ...

    def readall(self) -> Optional[bytes]:
        """Přečte všechno, co přišlo."""
        ...

    def readline(self) -> Optional[bytes]:
        """Přečte jeden řádek (do znaku nového řádku)."""
        ...

    def readinto(self, buf: bytearray, nbytes: Optional[int] = None) -> Optional[int]:
        """Přečte data do buf, vrací počet bajtů."""
        ...

    def write(self, buf: Union[str, bytes, bytearray]) -> Optional[int]:
        """Pošle text nebo bajty, vrací počet bajtů."""
        ...


i2c: MicroBitI2C
spi: MicroBitSPI
uart: MicroBitUART


# =========================================================
# Senzory
# =========================================================

class MicroBitAccelerometer:
    """
    Akcelerometr – zrychlení v mili-g (1000 = zemská tíže).

    Ležící deska displejem nahoru: x = 0, y = 0, z = -1024.

    Gesta: "up", "down", "left", "right", "face up", "face down",
    "freefall", "3g", "6g", "8g", "shake".
    """

    def get_x(self) -> int:
        """Zrychlení ve směru zleva doprava (mili-g)."""
        ...

    def get_y(self) -> int:
        """Zrychlení ve směru zepředu dozadu (mili-g)."""
        ...

    def get_z(self) -> int:
        """Zrychlení ve směru shora dolů (mili-g)."""
        ...

    def get_values(self) -> Tuple[int, int, int]:
        """Vrací (x, y, z) najednou."""
        ...

    def get_strength(self) -> int:
        """Velikost zrychlení bez ohledu na směr (mili-g)."""
        ...

    def current_gesture(self) -> str:
        """Gesto právě teď (např. "face up")."""
        ...

    def is_gesture(self, name: str) -> bool:
        """True, když právě teď probíhá gesto name."""
        ...

    def was_gesture(self, name: str) -> bool:
        """True, když gesto name proběhlo od posledního volání."""
        ...

    def get_gestures(self) -> Tuple[str, ...]:
        """Vrací gesta od posledního volání (nejstarší první) a seznam vyprázdní."""
        ...

    def set_range(self, value: int) -> None:
        """Rozsah měření v g: 2, 4 nebo 8."""
        ...


class MicroBitCompass:
    """Kompas (magnetometr). Před prvním použitím se kalibruje (hra na displeji)."""

    def calibrate(self) -> None:
        """Spustí kalibraci: nakláněním desky rozsviťte všechny body displeje."""
        ...

    def is_calibrated(self) -> bool:
        """True, když je kompas zkalibrovaný."""
        ...

    def clear_calibration(self) -> None:
        """Zapomene kalibraci."""
        ...

    def heading(self) -> int:
        """Směr, kam míří horní hrana desky: 0–359 stupňů (0 = sever)."""
        ...

    def get_x(self) -> int: ...
    def get_y(self) -> int: ...
    def get_z(self) -> int: ...

    def get_field_strength(self) -> int:
        """Síla magnetického pole v nanoteslách."""
        ...


class SoundEvent:
    """Události mikrofonu."""

    LOUD: SoundEvent
    """Zvuk zesílil nad práh."""
    QUIET: SoundEvent
    """Zvuk zeslábl pod práh."""


class MicroBitMicrophone:
    """Mikrofon (micro:bit v2)."""

    def sound_level(self) -> int:
        """Hlasitost okolí: 0 (ticho) až 255."""
        ...

    def current_event(self) -> Optional[SoundEvent]:
        """Poslední událost: SoundEvent.LOUD nebo SoundEvent.QUIET."""
        ...

    def is_event(self, event: SoundEvent) -> bool:
        """True, když je poslední událost event."""
        ...

    def was_event(self, event: SoundEvent) -> bool:
        """True, když událost event nastala od posledního volání."""
        ...

    def get_events(self) -> Tuple[SoundEvent, ...]:
        """Vrací události od posledního volání a seznam vyprázdní."""
        ...

    def set_threshold(self, event: SoundEvent, value: int) -> None:
        """Práh pro událost (0–255)."""
        ...


accelerometer: MicroBitAccelerometer
compass: MicroBitCompass
microphone: MicroBitMicrophone


# =========================================================
# Zvuk (micro:bit v2)
# =========================================================

class Sound:
    """Vestavěné zvuky: audio.play(Sound.HAPPY)."""

    GIGGLE: Sound
    HAPPY: Sound
    HELLO: Sound
    MYSTERIOUS: Sound
    SAD: Sound
    SLIDE: Sound
    SOARING: Sound
    SPRING: Sound
    TWINKLE: Sound
    YAWN: Sound


class _Speaker:
    """Reproduktor na desce."""

    def on(self) -> None:
        """Zapne reproduktor."""
        ...

    def off(self) -> None:
        """Vypne reproduktor (zvuk jde jen na pin0)."""
        ...

    def is_on(self) -> bool:
        """True, když je reproduktor zapnutý."""
        ...


class _Audio:
    """Přehrávání zvuků."""

    def play(self, source: Any, wait: bool = True, pin: Any = ..., return_pin: Any = None) -> None:
        """
        Přehraje zvuk (např. Sound.HAPPY).

        Args:
            source: vestavěný zvuk Sound.* nebo zvuková data.
            wait: True = počká na konec zvuku.
        """
        ...

    def is_playing(self) -> bool:
        """True, když zvuk ještě hraje."""
        ...

    def stop(self) -> None:
        """Zastaví zvuk."""
        ...


speaker: _Speaker
audio: _Audio
