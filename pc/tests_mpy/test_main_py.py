r"""Ukazkovy test: vychozi program main.py (MicroPython) na falesnem hardwaru.

Spusteni:  .\mpy test   (Linux/macOS: ./mpy.sh test)

Test bezi na PC. Modul machine (Pin, I2C, PWM, Timer) je falesny (pc/_fake)
a simuluje desku Pico:ed v2. Knihovna lib_mpy/picoed_v2_lib bezi beze zmeny
nad nim. Cas v testu sam neplyne - time.sleep() ho jen posune.

Pomocne funkce falesneho machine (na desce nejsou):
    machine.historie(25)        hodnoty zapsane na pin 25 (LED)
    machine.stiskni("a")        stiskne tlacitko A, stiskni("a", False) ho pusti
    machine.displej().svitici() co ukazuje displej ('#' sviti, '.' nesviti)

Stejny program na BBC micro:bit testuje test_main_py_microbit.py.
"""

import runpy
import time
import unittest
from pathlib import Path

import machine

MAIN_PY = Path(__file__).resolve().parents[2] / "main.py"


def nacti_main_py():
    """Provede main.py bez nekonecne smycky (ta bezi jen pri __name__ == "__main__")
    a vrati jeho promenne (led, display, board_name, ...)."""
    return runpy.run_path(str(MAIN_PY), run_name="test")


class TestMainPy(unittest.TestCase):

    def test_pozna_desku_picoed(self):
        promenne = nacti_main_py()
        self.assertEqual(promenne["board_name"], "ELECFREAKS Pico:ed v2")

    def test_led_se_zapina_a_vypina(self):
        led = nacti_main_py()["led"]
        led.on()
        led.off()
        # LED je na pinu 25 - falesny machine si pamatuje vsechny zapisy
        self.assertEqual(machine.historie(25)[-2:], [1, 0])

    def test_displej_ukaze_obrazek_a_smaze_se(self):
        from picoed_v2_lib import Image
        display = nacti_main_py()["display"]
        display.show(Image.HAPPY)
        self.assertIn("#", machine.displej().svitici())
        display.clear()
        self.assertNotIn("#", machine.displej().svitici())

    def test_tlacitko_a_se_pocita_po_odruseni_zakmitu(self):
        from picoed_v2_lib import Button, Gpio
        tlacitko = Button(Gpio.BUTTON_A)
        machine.stiskni("a")
        self.assertTrue(tlacitko.is_pressed())
        self.assertEqual(tlacitko.presses, 0)   # stisk se zapocita az po 20 ms (Timer)
        time.sleep_ms(30)
        self.assertEqual(tlacitko.presses, 1)
        machine.stiskni("a", False)
        self.assertFalse(tlacitko.is_pressed())

    def test_cas_v_testu_neplyne_sam(self):
        zacatek = time.ticks_ms()
        time.sleep(5)       # v testu se neceka - cas se jen posune o 5 s
        self.assertEqual(time.ticks_diff(time.ticks_ms(), zacatek), 5000)


if __name__ == "__main__":
    unittest.main()
