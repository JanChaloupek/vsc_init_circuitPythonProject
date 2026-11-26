"""Ukazkovy test: vychozi program code.py na falesnem hardwaru.

Spusteni:  .\\cpy test   (Linux/macOS: ./cpy.sh test)

Test bezi na PC. Moduly board, picoed, time, ... jsou falesne (pc/_fake):
nic nevypisuji, jen si pamatuji, co se s nimi delo, a cas v testu sam
neplyne - time.sleep() ho jen posune.
"""

import runpy
import time
import unittest
from pathlib import Path

import adafruit_ticks
import picoed

CODE_PY = Path(__file__).resolve().parents[2] / "code.py"


def nacti_code_py():
    """Provede code.py bez nekonecne smycky (ta bezi jen pri __name__ == "__main__")
    a vrati jeho promenne (led, display, board_name, ...)."""
    return runpy.run_path(str(CODE_PY), run_name="test")


class TestCodePy(unittest.TestCase):

    def test_pouzije_desku_picoed(self):
        promenne = nacti_code_py()
        self.assertEqual(promenne["board_name"], "ELECFREAKS Pico:ed (v1 / v2)")
        self.assertIs(promenne["led"], picoed.led)

    def test_led_se_prepina(self):
        led = nacti_code_py()["led"]
        led.off()
        led.toggle()
        led.toggle()
        # Falesna LED si pamatuje vsechny zmeny
        self.assertEqual(picoed.led.state_history[-3:], [False, True, False])

    def test_cas_v_testu_neplyne_sam(self):
        zacatek = adafruit_ticks.ticks_ms()
        time.sleep(5)       # v testu se neceka - cas se jen posune o 5 s
        self.assertEqual(adafruit_ticks.ticks_diff(adafruit_ticks.ticks_ms(), zacatek), 5000)


if __name__ == "__main__":
    unittest.main()
