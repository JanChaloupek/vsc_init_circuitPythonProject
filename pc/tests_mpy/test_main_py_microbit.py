r"""Ukazkovy test: vychozi program main.py na simulovanem BBC micro:bit.

Spusteni:  .\mpy test                        (vsechny testy z pc/tests_mpy)
           .\mpy test test_main_py_microbit  (jen tento soubor)

Testy bezi na simulovane desce Pico:ed v2. Tento test si v setUp vybere
micro:bit: nastav_desku("microbit"). Pak existuje (falesny) modul microbit
z pc/_fake/microbit.py a main.py desku pozna jako micro:bit. Pred dalsim
testem se deska vrati na Pico:ed.

Moduly pro micro:bit (microbit, music, radio, i vlastni moduly, ktere je
importuji) importuj az PO nastav_desku - v setUp nebo v testu. Pri nacitani
souboru s testy je jeste nastavena vychozi deska a `import microbit` by
skoncil chybou ImportError (jako na Picu).

Pomocne funkce falesneho microbit (na desce nejsou):
    microbit.stiskni("a")              stiskne tlacitko A, stiskni("a", False) ho pusti
    microbit.displej().svitici()       co ukazuje displej ('#' sviti, '.' nesviti)
    microbit.displej().text            posledni text z display.show / display.scroll
    microbit.nastav_analog(pin1, 512)  co vrati pin1.read_analog()
    microbit.pridej_i2c(0x38)          zarizeni na I2C (napr. senzory robota)
"""

import runpy
import time
import unittest
from pathlib import Path

from _fake._desky import nastav as nastav_desku

MAIN_PY = Path(__file__).resolve().parents[2] / "main.py"


def nacti_main_py():
    """Provede main.py bez nekonecne smycky (ta bezi jen pri __name__ == "__main__")
    a vrati jeho promenne (led, display, board_name, ...)."""
    return runpy.run_path(str(MAIN_PY), run_name="test")


class TestMainPyMicrobit(unittest.TestCase):

    def setUp(self):
        nastav_desku("microbit")
        import microbit
        self.microbit = microbit

    def test_pozna_desku_microbit(self):
        self.assertEqual(nacti_main_py()["board_name"], "BBC micro:bit")

    def test_led_je_prostredni_bod_displeje(self):
        led = nacti_main_py()["led"]
        led.on()
        self.assertEqual(self.microbit.displej().svitici(),
                         ".....\n.....\n..#..\n.....\n.....")
        led.toggle()
        self.assertEqual(self.microbit.display.get_pixel(2, 2), 0)

    def test_rolovani_textu_chvili_trva(self):
        display = nacti_main_py()["display"]
        zacatek = time.ticks_ms()
        display.scroll("ZSaPR")
        self.assertEqual(self.microbit.displej().text, "ZSaPR")
        # v testu se neceka - cas se jen posune o tolik, kolik by rolovani trvalo
        self.assertGreater(time.ticks_diff(time.ticks_ms(), zacatek), 2000)

    def test_tlacitko_a(self):
        from microbit import button_a
        self.microbit.stiskni("a")
        self.assertTrue(button_a.is_pressed())
        self.assertTrue(button_a.was_pressed())
        self.assertFalse(button_a.was_pressed())    # stisk uz se precetl
        self.microbit.stiskni("a", False)
        self.assertFalse(button_a.is_pressed())
        self.assertEqual(button_a.get_presses(), 1)


if __name__ == "__main__":
    unittest.main()
