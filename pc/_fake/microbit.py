# _fake/microbit.py

"""
Falešný modul microbit pro BBC micro:bit v2 s MicroPythonem (mpy sim, mpy test).

Program pro micro:bit běží na PC beze změny:

    from microbit import *
    display.scroll("Ahoj")
    while True:
        if button_a.was_pressed():
            display.show(Image.HEART)
        sleep(100)

Simuluje:
- display      displej 5 x 5 LED s jasem 0-9: show, scroll, set_pixel, get_pixel,
               clear, on / off, read_light_level
- Image        obrázky: Image.HEART, Image("09090:99999:..."), Image(5, 5),
               shift_left / right / up / down, crop, copy, invert, fill, blit, +, *
- button_a, button_b   tlačítka: is_pressed, was_pressed, get_presses
                       (v konzoli simulace klávesy a / b)
- pin0 - pin16, pin19, pin20   piny: read_digital, write_digital, read_analog
               (jen pin0-4 a pin10), write_analog, set_pull, is_touched (pin0-2)
- pin_logo     dotykové logo (v konzoli simulace klávesa l), pin_speaker
- i2c          sběrnice I2C (jsou na ní jen zařízení, která přidá test: pridej_i2c)
- uart, spi    uart.write píše do konzole (jako přes USB), spi nic nepřijme
- accelerometer, compass, microphone, speaker, audio, Sound, SoundEvent
- sleep(ms), running_time(), temperature(), set_volume(), reset(), panic()

Další moduly micro:bitu jsou v souborech microbit_*.py: music, neopixel,
radio a machine (na micro:bitu má jen time_pulse_us, reset, ...). Vybere je
_desky.py, když se simuluje deska "microbit" (mpy sim --microbit).

Čas je společný s ostatními falešnými moduly: v testu sám neběží
(sleep ho jen posune), v simulaci běží skutečně. Rolování textu
(display.scroll) trvá přibližně jako na desce.

Nesimulují se tvary písmen: display.show("A") a display.scroll("Ahoj")
se oznámí jako text (konzole: Displej: text "Ahoj"), body displeje
se přitom nerozsvítí. Dále se nesimuluje: speech, power, log.

Pomocné funkce pro testy (na desce nejsou):
    stiskni("a")                tlačítko A (stiskni("a", False) ho pustí; "l" = logo)
    displej().svitici()         co ukazuje displej ('#' svítí, '.' nesvítí)
    displej().text              poslední text z show / scroll
    nastav_vstup(pin0, 1)       co je na pinu zvenku (0, 1, None = nic)
    nastav_analog(pin1, 512)    co vrátí read_analog() (0-1023)
    nastav_pulz(pin2, 580)      co vrátí machine.time_pulse_us (např. ultrazvuk)
    dotkni(pin0)                dotyk pinu / loga (dotkni(pin0, False) = pustit)
    historie(pin0)              všechny hodnoty zapsané na pin (write_digital / write_analog)
    pridej_i2c(0x38)            zařízení na I2C (ZarizeniI2C s 256 registry)
    nastav_naklon(x, y, z)      akcelerometr v mili-g (vodorovně: 0, 0, -1024)
    nastav_gesto("shake")       gesto akcelerometru
    nastav_kompas(90)           kam ukazuje kompas (stupně)
    nastav_teplotu(25), nastav_svetlo(120), nastav_hluk(200)
"""

import sys

try:
    from . import _rezim                        # nacteno jako balicek _fake
    from . import utime as _utime
except ImportError:
    import _rezim                               # nacteno primo ze slozky _fake
    import utime as _utime


__all__ = [
    "display", "Image", "button_a", "button_b",
    "pin0", "pin1", "pin2", "pin3", "pin4", "pin5", "pin6", "pin7", "pin8", "pin9", "pin10",
    "pin11", "pin12", "pin13", "pin14", "pin15", "pin16", "pin19", "pin20", "pin_logo", "pin_speaker",
    "i2c", "uart", "spi", "accelerometer", "compass", "microphone", "speaker", "audio",
    "Sound", "SoundEvent", "sleep", "running_time", "temperature", "set_volume", "reset", "panic",
]

_k_resetu = []          # objekty s metodou _reset (vrati je do vychoziho stavu)


def _zarizeni(objekt):
    _k_resetu.append(objekt)
    return objekt


def _rozsah(hodnota, nejmene, nejvice, chyba):
    hodnota = int(hodnota)
    if not nejmene <= hodnota <= nejvice:
        raise ValueError(chyba)
    return hodnota


# =========================================================
# Image
# =========================================================

class Image:
    """Obrazek z bodu s jasem 0-9. Image("09090:99999:99999:09990:00900") je srdce."""

    def __init__(self, *args):
        self._jen_cteni = False
        if not args:
            self._w, self._h, self._b = 5, 5, [0] * 25
        elif len(args) == 1 and isinstance(args[0], str):
            radky = args[0].replace("\n", ":").split(":")
            while radky and radky[-1] == "":
                radky.pop()
            self._w = max((len(r) for r in radky), default=0)
            self._h = len(radky)
            self._b = []
            for r in radky:
                for znak in r.ljust(self._w, "0"):
                    if znak == " ":
                        znak = "0"
                    if not znak.isdigit():
                        raise ValueError("unexpected character in Image definition")
                    self._b.append(int(znak))
        elif len(args) in (2, 3):
            self._w, self._h = int(args[0]), int(args[1])
            if self._w < 0 or self._h < 0:
                raise ValueError("image width and height must be positive")
            if len(args) == 3:
                data = list(args[2])
                if len(data) != self._w * self._h:
                    raise ValueError("image data is incorrect size")
                self._b = [_rozsah(v, 0, 9, "brightness out of bounds") for v in data]
            else:
                self._b = [0] * (self._w * self._h)
        else:
            raise TypeError("Image(s) or Image(width, height[, buffer])")

    # --- velikost a body ---
    def width(self):
        return self._w

    def height(self):
        return self._h

    def _uvnitr(self, x, y):
        return 0 <= x < self._w and 0 <= y < self._h

    def get_pixel(self, x, y):
        if not self._uvnitr(x, y):
            raise ValueError("index cannot be negative" if x < 0 or y < 0 else "index too large")
        return self._b[y * self._w + x]

    def set_pixel(self, x, y, value):
        if self._jen_cteni:
            raise TypeError("This image cannot be modified. Try copying it first.")
        if not self._uvnitr(x, y):
            raise ValueError("index cannot be negative" if x < 0 or y < 0 else "index too large")
        self._b[y * self._w + x] = _rozsah(value, 0, 9, "brightness out of bounds")

    def fill(self, value):
        if self._jen_cteni:
            raise TypeError("This image cannot be modified. Try copying it first.")
        v = _rozsah(value, 0, 9, "brightness out of bounds")
        self._b = [v] * (self._w * self._h)

    # --- nove obrazky ---
    def _novy(self, w, h, bod):
        img = Image(w, h)
        img._b = [bod(x, y) for y in range(h) for x in range(w)]
        return img

    def _bod(self, x, y):
        return self._b[y * self._w + x] if self._uvnitr(x, y) else 0

    def copy(self):
        return self._novy(self._w, self._h, self._bod)

    def crop(self, x, y, w, h):
        return self._novy(w, h, lambda i, j: self._bod(x + i, y + j))

    def shift_left(self, n):
        return self._novy(self._w, self._h, lambda x, y: self._bod(x + n, y))

    def shift_right(self, n):
        return self.shift_left(-n)

    def shift_up(self, n):
        return self._novy(self._w, self._h, lambda x, y: self._bod(x, y + n))

    def shift_down(self, n):
        return self.shift_up(-n)

    def invert(self):
        return self._novy(self._w, self._h, lambda x, y: 9 - self._bod(x, y))

    def blit(self, src, x, y, w, h, xdest=0, ydest=0):
        if self._jen_cteni:
            raise TypeError("This image cannot be modified. Try copying it first.")
        for j in range(h):
            for i in range(w):
                if self._uvnitr(xdest + i, ydest + j):
                    self._b[(ydest + j) * self._w + xdest + i] = src._bod(x + i, y + j)

    def __add__(self, other):
        if not isinstance(other, Image) or (other._w, other._h) != (self._w, self._h):
            raise ValueError("images must be the same size")
        return self._novy(self._w, self._h, lambda x, y: min(9, self._bod(x, y) + other._bod(x, y)))

    def __mul__(self, cislo):
        cislo = float(cislo)
        if cislo < 0:
            raise ValueError("brightness multiplier must not be negative")
        return self._novy(self._w, self._h, lambda x, y: min(9, int(self._bod(x, y) * cislo)))

    def __truediv__(self, cislo):
        return self * (1 / float(cislo))

    # --- porovnani a vypis ---
    def __eq__(self, other):
        return isinstance(other, Image) and (self._w, self._h, self._b) == (other._w, other._h, other._b)

    def __hash__(self):
        return id(self)

    def _radky(self):
        return ["".join(str(v) for v in self._b[y * self._w:(y + 1) * self._w]) for y in range(self._h)]

    def __repr__(self):
        return "Image('" + "".join(r + ":" for r in self._radky()) + "')"

    def __str__(self):
        return "Image(\n" + "".join("    '" + r + ":'\n" for r in self._radky()) + ")"


# Vestavene obrazky (stejna jmena jako na micro:bitu; nedaji se menit - copy())
_OBRAZKY = {
    "HEART": "09090:99999:99999:09990:00900", "HEART_SMALL": "00000:09090:09990:00900:00000",
    "HAPPY": "00000:09090:00000:90009:09990", "SMILE": "00000:00000:00000:90009:09990",
    "SAD": "00000:09090:00000:09990:90009", "CONFUSED": "00000:09090:00000:09090:90909",
    "ANGRY": "90009:09090:00000:99999:90909", "ASLEEP": "00000:99099:00000:09990:00000",
    "SURPRISED": "09090:00000:00900:09090:00900", "SILLY": "90009:00000:99999:00909:00999",
    "FABULOUS": "99999:99099:00000:09090:09990", "MEH": "09090:00000:00090:00900:09000",
    "YES": "00000:00009:00090:90900:09000", "NO": "90009:09090:00900:09090:90009",
    "CLOCK12": "00900:00900:00900:00000:00000", "CLOCK1": "00090:00090:00900:00000:00000",
    "CLOCK2": "00000:00099:00900:00000:00000", "CLOCK3": "00000:00000:00999:00000:00000",
    "CLOCK4": "00000:00000:00900:00099:00000", "CLOCK5": "00000:00000:00900:00090:00090",
    "CLOCK6": "00000:00000:00900:00900:00900", "CLOCK7": "00000:00000:00900:09000:09000",
    "CLOCK8": "00000:00000:00900:99000:00000", "CLOCK9": "00000:00000:99900:00000:00000",
    "CLOCK10": "00000:99000:00900:00000:00000", "CLOCK11": "09000:09000:00900:00000:00000",
    "ARROW_N": "00900:09990:90909:00900:00900", "ARROW_NE": "00999:00099:00909:09000:90000",
    "ARROW_E": "00900:00090:99999:00090:00900", "ARROW_SE": "90000:09000:00909:00099:00999",
    "ARROW_S": "00900:00900:90909:09990:00900", "ARROW_SW": "00009:00090:90900:99000:99900",
    "ARROW_W": "00900:09000:99999:09000:00900", "ARROW_NW": "99900:99000:90900:00090:00009",
    "TRIANGLE": "00000:00900:09090:99999:00000", "TRIANGLE_LEFT": "90000:99000:90900:90090:99999",
    "CHESSBOARD": "09090:90909:09090:90909:09090", "DIAMOND": "00900:09090:90009:09090:00900",
    "DIAMOND_SMALL": "00000:00900:09090:00900:00000", "SQUARE": "99999:90009:90009:90009:99999",
    "SQUARE_SMALL": "00000:09990:09090:09990:00000", "RABBIT": "90900:90900:99990:99090:99990",
    "COW": "90009:90009:99999:09990:00900", "MUSIC_CROTCHET": "00900:00900:00900:99900:99900",
    "MUSIC_QUAVER": "00900:00990:00909:99900:99900", "MUSIC_QUAVERS": "09999:09009:09009:99099:99099",
    "PITCHFORK": "90909:90909:99999:00900:00900", "XMAS": "00900:09990:00900:09990:99999",
    "PACMAN": "09999:99090:99900:99990:09999", "TARGET": "00900:09990:99099:09990:00900",
    "TSHIRT": "99099:99999:09990:09990:09990", "ROLLERSKATE": "00099:00099:99999:99999:09090",
    "DUCK": "09900:99900:09999:09990:00000", "HOUSE": "00900:09990:99999:09990:09090",
    "TORTOISE": "00000:09990:99999:09090:00000", "BUTTERFLY": "99099:99999:00900:99999:99099",
    "STICKFIGURE": "00900:99999:00900:09090:90009", "GHOST": "99999:90909:99999:99999:90909",
    "SWORD": "00900:00900:00900:09990:00900", "GIRAFFE": "99000:09000:09000:09990:09090",
    "SKULL": "09990:90909:99999:09990:09990", "UMBRELLA": "09990:99999:00900:90900:09900",
    "SNAKE": "99000:99099:09090:09990:00000", "SCISSORS": "99009:99090:00900:99090:99009",
}
for _jmeno, _data in _OBRAZKY.items():
    _img = Image(_data)
    _img._jen_cteni = True
    setattr(Image, _jmeno, _img)
Image.ALL_CLOCKS = tuple(getattr(Image, "CLOCK%d" % h) for h in (12, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11))
Image.ALL_ARROWS = tuple(getattr(Image, "ARROW_" + s) for s in ("N", "NE", "E", "SE", "S", "SW", "W", "NW"))
del _jmeno, _data, _img


# =========================================================
# Displej 5 x 5
# =========================================================

def _jen_v_simulaci_navzdy():
    """loop=True s wait=True: na desce by to bezelo navzdy. V simulaci se
    ceka do konce (q / Ctrl+C), v testu se vrati hned (cas sam neplyne)."""
    if _rezim.je_simulace():
        while True:
            _rezim.realne_cekej(1)


class MicroBitDisplay:
    """Displej 5 x 5 LED, jas bodu 0 (nesviti) az 9."""

    def __init__(self):
        self._reset()

    def _reset(self):
        self._b = [[0] * 5 for _ in range(5)]
        self._zapnuty = True
        self._svetlo = 0
        self.text = None            # posledni text z show / scroll (pro testy)

    def _oznam(self):
        _rezim.oznam("displej", "obraz", self.obraz())

    def _nastav(self, img):
        self._b = [[img._bod(x, y) for x in range(5)] for y in range(5)]
        self._oznam()

    def _text(self, text):
        self.text = text
        self._b = [[0] * 5 for _ in range(5)]   # tvary pismen se nesimuluji
        _rezim.oznam("displej", "scroll", text)

    def show(self, image, delay=400, *, wait=True, loop=False, clear=False):
        """Obrazek, cislo, text (znak po znaku) nebo seznam obrazku (animace)."""
        if isinstance(image, (int, float)):
            image = str(image)
        if isinstance(image, Image):
            self._nastav(image)
            return
        if isinstance(image, str):
            if not image:
                return
            self._text(image)
            if len(image) > 1 and wait:
                if loop:
                    _jen_v_simulaci_navzdy()
                    return
                _utime.sleep_ms(len(image) * int(delay))
                if clear:
                    self.clear()
            return
        snimky = list(image)
        while True:
            for snimek in snimky:
                if isinstance(snimek, Image):
                    self._nastav(snimek)
                else:
                    self._text(str(snimek))
                if not wait:
                    return          # na desce by animace bezela na pozadi
                _utime.sleep_ms(int(delay))
            if not loop:
                break
            if not _rezim.je_simulace():
                return
        if clear:
            self.clear()

    def scroll(self, text, delay=150, *, wait=True, loop=False, monospace=False):
        """Text projede displejem zprava doleva (delay = ms na posun o 1 sloupec)."""
        text = str(text)
        self._text(text)
        if not wait:
            return
        if loop:
            _jen_v_simulaci_navzdy()
            return
        # pismeno ma 5 sloupcu + 1 mezera (proporcionalni pismo v prumeru o sloupec min)
        sloupcu = len(text) * (6 if monospace else 5) + 5
        _utime.sleep_ms(sloupcu * int(delay))

    def clear(self):
        self._b = [[0] * 5 for _ in range(5)]
        self._oznam()

    def set_pixel(self, x, y, value):
        if not (0 <= x < 5 and 0 <= y < 5):
            raise ValueError("index out of bounds")
        v = _rozsah(value, 0, 9, "brightness out of bounds")
        if self._b[y][x] != v:
            self._b[y][x] = v
            self._oznam()

    def get_pixel(self, x, y):
        if not (0 <= x < 5 and 0 <= y < 5):
            raise ValueError("index out of bounds")
        return self._b[y][x]

    def on(self):
        self._zapnuty = True

    def off(self):
        self._zapnuty = False

    def is_on(self):
        return self._zapnuty

    def read_light_level(self):
        return self._svetlo

    # --- jen na PC (pro testy) ---
    def obraz(self):
        """Co displej ukazuje: 5 radku po 5 hodnotach jasu (0-9)."""
        return [radek[:] for radek in self._b]

    def svitici(self):
        """Obraz jako text: '#' sviti, '.' nesviti (radky oddelene znakem \\n)."""
        return "\n".join("".join("#" if v else "." for v in radek) for radek in self._b)


display = _zarizeni(MicroBitDisplay())


# =========================================================
# Tlacitka
# =========================================================

class MicroBitButton:
    """Tlacitko A nebo B."""

    def __init__(self, jmeno):
        self._jmeno = jmeno
        self._reset()

    def _reset(self):
        self._dole = False
        self._stisku = 0
        self._bylo = False

    def _stisk(self, stisknuto):
        stisknuto = bool(stisknuto)
        if stisknuto == self._dole:
            return
        if stisknuto:
            self._stisku += 1
            self._bylo = True
        self._dole = stisknuto
        _rezim.oznam("tlacitko", self._jmeno, stisknuto)

    def is_pressed(self):
        """True, dokud je tlacitko stisknute."""
        return self._dole

    def was_pressed(self):
        """True, kdyz bylo od posledniho volani stisknuto."""
        bylo, self._bylo = self._bylo, False
        return bylo

    def get_presses(self):
        """Pocet stisku od posledniho volani (pocitadlo se vynuluje)."""
        pocet, self._stisku = self._stisku, 0
        return pocet


button_a = _zarizeni(MicroBitButton("BUTTON_A"))
button_b = _zarizeni(MicroBitButton("BUTTON_B"))


# =========================================================
# Piny
# =========================================================

class MicroBitDigitalPin:
    """Digitalni pin (umi i write_analog = PWM)."""

    NO_PULL = 0
    PULL_DOWN = 1
    PULL_UP = 3

    def __init__(self, cislo, jmeno=None):
        self._cislo = cislo
        self._jmeno = jmeno or "P%d" % cislo
        self._reset()

    def _reset(self):
        self._mode = "unused"
        self._vystup = 0
        self._pwm = 0
        self._perioda_us = 20_000
        self._pull = self.PULL_DOWN
        self._zvenku = None         # co je na pinu zvenku (None = nic)
        self._analog = 0            # co vrati read_analog
        self._pulz = None           # co vrati machine.time_pulse_us
        self._dotyk = False
        self._historie = []

    def write_digital(self, value):
        v = 1 if value else 0
        zmena = v != self._vystup or self._mode != "write_digital"
        self._mode = "write_digital"
        self._vystup = v
        self._historie.append(v)
        if zmena:
            _rezim.oznam("pin", self._jmeno, v)

    def _vstup(self):
        if self._zvenku is not None:
            return self._zvenku
        return 1 if self._pull == self.PULL_UP else 0

    def read_digital(self):
        self._mode = "read_digital"
        return self._vstup()

    def set_pull(self, value):
        if value not in (self.NO_PULL, self.PULL_DOWN, self.PULL_UP):
            raise ValueError("invalid pull")
        self._pull = value

    def get_pull(self):
        return self._pull

    def get_mode(self):
        return self._mode

    def write_analog(self, value):
        v = int(value)
        if not 0 <= v <= 1023:
            raise ValueError("value must be between 0 and 1023")
        zmena = v != self._pwm or self._mode != "write_analog"
        self._mode = "write_analog"
        self._pwm = v
        self._historie.append(v)
        if zmena:
            _rezim.oznam("pwm", self._jmeno, (round(1_000_000 / self._perioda_us), v * 65535 // 1023))

    def set_analog_period(self, period):
        self.set_analog_period_microseconds(int(period) * 1000)

    def set_analog_period_microseconds(self, period):
        period = int(period)
        if period < 256:
            raise ValueError("invalid period")
        self._perioda_us = period

    def get_analog_period_microseconds(self):
        return self._perioda_us


class MicroBitAnalogDigitalPin(MicroBitDigitalPin):
    """Pin s analogovym vstupem (pin0-pin4, pin10)."""

    def read_analog(self):
        """Napeti na pinu 0-1023 (0 V - 3,3 V)."""
        self._mode = "read_analog"
        return self._analog


class MicroBitTouchPin(MicroBitAnalogDigitalPin):
    """Pin s analogovym vstupem a dotykem (pin0-pin2)."""

    RESISTIVE = 0
    CAPACITIVE = 1

    def is_touched(self):
        self._mode = "touch"
        return self._dotyk

    def set_touch_mode(self, value):
        if value not in (self.RESISTIVE, self.CAPACITIVE):
            raise ValueError("invalid touch mode")


class _TlacitkovyPin(MicroBitDigitalPin):
    """pin5 a pin11: jsou na nich tlacitka A a B (stisk = 0, jinak pull-up desky = 1)."""

    def __init__(self, cislo, tlacitko):
        self._tlacitko = tlacitko
        super().__init__(cislo)

    def _vstup(self):
        if self._zvenku is not None:
            return self._zvenku
        return 0 if self._tlacitko.is_pressed() else 1


class MicroBitTouchOnlyPin:
    """Dotykove logo micro:bitu v2."""

    RESISTIVE = 0
    CAPACITIVE = 1

    def __init__(self):
        self._jmeno = "LOGO"
        self._reset()

    def _reset(self):
        self._dotyk = False
        self._pulz = None

    def _stisk(self, stisknuto):
        stisknuto = bool(stisknuto)
        if stisknuto != self._dotyk:
            self._dotyk = stisknuto
            _rezim.oznam("tlacitko", self._jmeno, stisknuto)

    def is_touched(self):
        return self._dotyk

    def set_touch_mode(self, value):
        if value not in (self.RESISTIVE, self.CAPACITIVE):
            raise ValueError("invalid touch mode")


pin0 = _zarizeni(MicroBitTouchPin(0))
pin1 = _zarizeni(MicroBitTouchPin(1))
pin2 = _zarizeni(MicroBitTouchPin(2))
pin3 = _zarizeni(MicroBitAnalogDigitalPin(3))
pin4 = _zarizeni(MicroBitAnalogDigitalPin(4))
pin5 = _zarizeni(_TlacitkovyPin(5, button_a))
pin6 = _zarizeni(MicroBitDigitalPin(6))
pin7 = _zarizeni(MicroBitDigitalPin(7))
pin8 = _zarizeni(MicroBitDigitalPin(8))
pin9 = _zarizeni(MicroBitDigitalPin(9))
pin10 = _zarizeni(MicroBitAnalogDigitalPin(10))
pin11 = _zarizeni(_TlacitkovyPin(11, button_b))
pin12 = _zarizeni(MicroBitDigitalPin(12))
pin13 = _zarizeni(MicroBitDigitalPin(13))
pin14 = _zarizeni(MicroBitDigitalPin(14))
pin15 = _zarizeni(MicroBitDigitalPin(15))
pin16 = _zarizeni(MicroBitDigitalPin(16))
pin19 = _zarizeni(MicroBitDigitalPin(19))
pin20 = _zarizeni(MicroBitDigitalPin(20))
pin_logo = _zarizeni(MicroBitTouchOnlyPin())
pin_speaker = _zarizeni(MicroBitDigitalPin(27, "SPEAKER"))


# =========================================================
# I2C, SPI, UART
# =========================================================

class ZarizeniI2C:
    """Obecne zarizeni na I2C: 256 registru (stejne jako v machine.py).

    Zapis: prvni bajt je cislo registru, dalsi bajty se zapisou od nej.
    Cteni pokracuje od registru za poslednim zapisem. Hodnoty jsou v .registry.
    Test si muze udelat vlastni zarizeni (metody zapis a cti) a pridat ho
    funkci pridej_i2c()."""

    def __init__(self):
        self.registry = bytearray(256)
        self._ukazatel = 0

    def zapis(self, registr, data):
        for i, b in enumerate(data):
            self.registry[(registr + i) & 0xFF] = b
        self._ukazatel = (registr + len(data)) & 0xFF

    def cti(self, registr, pocet):
        if registr is None:
            registr = self._ukazatel
        data = bytes(self.registry[(registr + i) & 0xFF] for i in range(pocet))
        self._ukazatel = (registr + pocet) & 0xFF
        return data


class MicroBitI2C:
    """Sbernice I2C (pin19 = SCL, pin20 = SDA)."""

    def __init__(self):
        self._reset()

    def _reset(self):
        self._freq = 100_000
        self._zarizeni = {}
        self._dluh_us = 0

    def init(self, freq=100_000, sda=None, scl=None):
        self._freq = int(freq)

    def scan(self):
        return sorted(self._zarizeni)

    def _najdi(self, addr):
        zarizeni = self._zarizeni.get(addr)
        if zarizeni is None:
            raise OSError(19, "ENODEV")     # jako na desce: na adrese nikdo neni
        return zarizeni

    def _cas_prenosu(self, bajtu):
        # Prenos po sbernici trva (9 bitu na bajt); kratke useky se scitaji
        self._dluh_us += (bajtu + 1) * 9 * 1_000_000 // max(1, self._freq) + 10
        if self._dluh_us >= 2000:
            cekej, self._dluh_us = self._dluh_us, 0
            _utime.sleep_us(cekej)

    def read(self, addr, n, repeat=False):
        zarizeni = self._najdi(addr)
        self._cas_prenosu(n)
        return bytes(zarizeni.cti(None, n))

    def write(self, addr, buf, repeat=False):
        data = bytes(buf)
        zarizeni = self._najdi(addr)
        self._cas_prenosu(len(data))
        if data:
            zarizeni.zapis(data[0], data[1:])


class MicroBitSPI:
    """Sbernice SPI. Nic na ni neni: read vrati bajty `write`, zapis se zahodi."""

    def init(self, baudrate=1_000_000, bits=8, mode=0, sclk=None, mosi=None, miso=None):
        pass

    def write(self, buf):
        pass

    def read(self, nbytes, write=0):
        return bytes([write]) * nbytes

    def write_readinto(self, out, in_):
        for i in range(len(in_)):
            in_[i] = 0


class MicroBitUART:
    """Seriova linka. Bez tx / rx jde pres USB do PC - write() pise do konzole."""

    ODD = 1
    EVEN = 0

    def __init__(self):
        self._reset()

    def _reset(self):
        self._usb = True

    def init(self, baudrate=9600, bits=8, parity=None, stop=1, *, tx=None, rx=None):
        self._usb = tx is None and rx is None

    def any(self):
        return False

    def read(self, nbytes=None):
        return None

    def readall(self):
        return None

    def readline(self):
        return None

    def readinto(self, buf, nbytes=None):
        return None

    def write(self, buf):
        text = buf if isinstance(buf, str) else bytes(buf).decode("utf-8", "replace")
        if self._usb:
            sys.stdout.write(text)
            sys.stdout.flush()
        else:
            _rezim.oznam("uart", "tx", text)
        return len(buf)


i2c = _zarizeni(MicroBitI2C())
spi = MicroBitSPI()
uart = _zarizeni(MicroBitUART())


# =========================================================
# Senzory
# =========================================================

_GESTA = ("up", "down", "left", "right", "face up", "face down", "freefall", "3g", "6g", "8g", "shake")


class MicroBitAccelerometer:
    """Akcelerometr v mili-g: vodorovne lezici deska = (0, 0, -1024)."""

    def __init__(self):
        self._reset()

    def _reset(self):
        self._xyz = (0, 0, -1024)
        self._gesto = "face up"
        self._gesta = []
        self._rozsah = 2

    def get_x(self):
        return self._xyz[0]

    def get_y(self):
        return self._xyz[1]

    def get_z(self):
        return self._xyz[2]

    def get_values(self):
        return self._xyz

    def get_strength(self):
        return int(sum(v * v for v in self._xyz) ** 0.5)

    def current_gesture(self):
        return self._gesto

    def is_gesture(self, name):
        return name == self._gesto

    def was_gesture(self, name):
        bylo = name in self._gesta
        self._gesta = [g for g in self._gesta if g != name]
        return bylo

    def get_gestures(self):
        gesta, self._gesta = tuple(self._gesta), []
        return gesta

    def set_range(self, value):
        self._rozsah = int(value)


class MicroBitCompass:
    """Kompas. heading() vrati smer, ktery nastavi test (nastav_kompas)."""

    def __init__(self):
        self._reset()

    def _reset(self):
        self._smer = 0
        self._kalibrovany = True

    def calibrate(self):
        self._kalibrovany = True

    def is_calibrated(self):
        return self._kalibrovany

    def clear_calibration(self):
        self._kalibrovany = False

    def heading(self):
        return self._smer

    def get_x(self):
        return 0

    def get_y(self):
        return 0

    def get_z(self):
        return 0

    def get_field_strength(self):
        return 50_000


class SoundEvent:
    """Udalosti mikrofonu."""

    def __init__(self, jmeno):
        self._jmeno = jmeno

    def __repr__(self):
        return "SoundEvent('%s')" % self._jmeno


SoundEvent.LOUD = SoundEvent("loud")
SoundEvent.QUIET = SoundEvent("quiet")


class MicroBitMicrophone:
    """Mikrofon: sound_level() 0-255, udalosti LOUD / QUIET podle prahu."""

    def __init__(self):
        self._reset()

    def _reset(self):
        self._hluk = 0
        self._prahy = {"loud": 128, "quiet": 64}
        self._udalosti = []
        self._udalost = SoundEvent.QUIET

    def _nastav(self, hluk):
        self._hluk = _rozsah(hluk, 0, 255, "sound level out of range")
        if self._udalost is SoundEvent.QUIET and self._hluk >= self._prahy["loud"]:
            self._udalost = SoundEvent.LOUD
            self._udalosti.append(SoundEvent.LOUD)
        elif self._udalost is SoundEvent.LOUD and self._hluk <= self._prahy["quiet"]:
            self._udalost = SoundEvent.QUIET
            self._udalosti.append(SoundEvent.QUIET)

    def sound_level(self):
        return self._hluk

    def current_event(self):
        return self._udalost

    def is_event(self, event):
        return event is self._udalost

    def was_event(self, event):
        bylo = event in self._udalosti
        self._udalosti = [u for u in self._udalosti if u is not event]
        return bylo

    def get_events(self):
        udalosti, self._udalosti = tuple(self._udalosti), []
        return udalosti

    def set_threshold(self, event, value):
        self._prahy[event._jmeno] = _rozsah(value, 0, 255, "threshold out of range")


accelerometer = _zarizeni(MicroBitAccelerometer())
compass = _zarizeni(MicroBitCompass())
microphone = _zarizeni(MicroBitMicrophone())


# =========================================================
# Zvuk: reproduktor, audio, Sound
# =========================================================

class Sound:
    """Vestavene zvuky micro:bitu v2 (audio.play(Sound.HAPPY))."""

    def __init__(self, jmeno):
        self._jmeno = jmeno

    def __repr__(self):
        return "Sound." + self._jmeno


for _jmeno in ("GIGGLE", "HAPPY", "HELLO", "MYSTERIOUS", "SAD", "SLIDE", "SOARING", "SPRING", "TWINKLE", "YAWN"):
    setattr(Sound, _jmeno, Sound(_jmeno))
del _jmeno

_DELKA_ZVUKU_MS = 1000          # vestavene zvuky trvaji asi 1 s


class _Audio:
    """audio.play(Sound.HAPPY) - zvuk se jen oznami (konzole: Bzucak: melodie Sound.HAPPY)."""

    def __init__(self):
        self._reset()

    def _reset(self):
        self._hraje = False

    def play(self, source, wait=True, pin=None, return_pin=None):
        _rezim.oznam("bzucak", "play", repr(source) if isinstance(source, Sound) else source)
        if wait:
            _utime.sleep_ms(_DELKA_ZVUKU_MS)
        else:
            self._hraje = True

    def is_playing(self):
        return self._hraje

    def stop(self):
        self._hraje = False
        _rezim.oznam("bzucak", "stop", None)


class _Speaker:
    """Reproduktor micro:bitu v2."""

    def __init__(self):
        self._reset()

    def _reset(self):
        self._zapnuty = True

    def on(self):
        self._zapnuty = True

    def off(self):
        self._zapnuty = False

    def is_on(self):
        return self._zapnuty


audio = _zarizeni(_Audio())
speaker = _zarizeni(_Speaker())


# =========================================================
# Funkce modulu microbit
# =========================================================

_stav = {"teplota": 21, "hlasitost": 255}


def sleep(ms):
    """Pocka ms MILISEKUND (pozor: time.sleep() bere sekundy)."""
    ms = int(ms)                # jako na desce: sleep(0.5) ceka 0 ms
    if ms > 0:
        _utime.sleep_ms(ms)


def running_time():
    """Milisekundy od spusteni desky."""
    return _utime.ticks_ms()


def temperature():
    """Teplota procesoru ve stupnich Celsia."""
    return _stav["teplota"]


def set_volume(value):
    _stav["hlasitost"] = max(0, min(255, int(value)))


def reset():
    print("microbit.reset() - deska by se restartovala, simulace konci.")
    raise SystemExit(0)


def panic(n=0):
    print("microbit.panic(%d) - deska by ukazovala smutny oblicej a cislo %d, simulace konci." % (n, n))
    raise SystemExit(1)


# =========================================================
# Pomocne funkce pro testy (na desce nejsou)
# =========================================================

def displej():
    """Model displeje: obraz(), svitici(), text."""
    return display


def stiskni(klavesa, stisknuto=True):
    """Stiskne / pusti tlacitko: stiskni("a"), stiskni("b", False), "l" = dotyk loga."""
    if not _rezim.stiskni(klavesa, stisknuto):
        raise ValueError("micro:bit nema tlacitko %r (a, b, l = logo)" % (klavesa,))


def nastav_vstup(pin, uroven):
    """Co je na pinu zvenku: 0, 1 nebo None (nic - plati set_pull)."""
    pin._zvenku = None if uroven is None else (1 if uroven else 0)


def nastav_analog(pin, hodnota):
    """Co vrati pin.read_analog() (0-1023)."""
    if not isinstance(pin, MicroBitAnalogDigitalPin):
        raise ValueError("pin %s nema analogovy vstup (jen pin0-pin4 a pin10)" % pin._jmeno)
    pin._analog = _rozsah(hodnota, 0, 1023, "hodnota musi byt 0-1023")


def nastav_pulz(pin, us):
    """Delka pulzu, kterou vrati machine.time_pulse_us(pin, ...); None = zadny pulz."""
    pin._pulz = None if us is None else int(us)


def dotkni(pin, dotyk=True):
    """Dotyk pinu pin0-pin2 nebo loga (pin_logo)."""
    if isinstance(pin, MicroBitTouchOnlyPin):
        pin._stisk(dotyk)
    elif isinstance(pin, MicroBitTouchPin):
        pin._dotyk = bool(dotyk)
    else:
        raise ValueError("pin %s neni dotykovy (jen pin0-pin2 a pin_logo)" % pin._jmeno)


def historie(pin):
    """Vsechny hodnoty zapsane na pin (write_digital 0/1, write_analog 0-1023)."""
    return list(pin._historie)


def pridej_i2c(adresa, zarizeni=None):
    """Pripoji zarizeni na I2C (vychozi: ZarizeniI2C s 256 registry) a vrati ho."""
    if zarizeni is None:
        zarizeni = ZarizeniI2C()
    i2c._zarizeni[adresa] = zarizeni
    return zarizeni


def nastav_naklon(x, y, z):
    """Co nameri akcelerometr (mili-g). Vodorovne: (0, 0, -1024)."""
    accelerometer._xyz = (int(x), int(y), int(z))


def nastav_gesto(gesto):
    """Gesto akcelerometru: "shake", "face up", "left", ... (zapocita se pro was_gesture)."""
    if gesto not in _GESTA:
        raise ValueError("nezname gesto %r (%s)" % (gesto, ", ".join(_GESTA)))
    accelerometer._gesto = gesto
    accelerometer._gesta.append(gesto)


def nastav_kompas(stupne):
    compass._smer = int(stupne) % 360


def nastav_teplotu(stupne):
    _stav["teplota"] = int(stupne)


def nastav_svetlo(hodnota):
    """Co vrati display.read_light_level() (0-255)."""
    display._svetlo = _rozsah(hodnota, 0, 255, "hodnota musi byt 0-255")


def nastav_hluk(hodnota):
    """Co vrati microphone.sound_level() (0-255); prah LOUD je 128."""
    microphone._nastav(hodnota)


def _reset():
    """Vychozi stav desky (pred kazdym testem a pri nastaveni desky)."""
    if _rezim.deska != "microbit":
        return
    for objekt in _k_resetu:
        objekt._reset()
    _stav.update(teplota=21, hlasitost=255)
    # Klavesy a / b / l v konzoli simulace
    _rezim.registruj_tlacitko("a", button_a._stisk)
    _rezim.registruj_tlacitko("b", button_b._stisk)
    _rezim.registruj_tlacitko("l", pin_logo._stisk)


_rezim.pri_resetu(_reset)
