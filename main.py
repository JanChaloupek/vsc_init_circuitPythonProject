# Starter program pro MicroPython na desce Pico:ed v2
# (Pro CircuitPython je hlavním spouštěným souborem code.py)

import time
from picoed_v2_lib import Display, Led

display = Display()
led = Led()

if __name__ == "__main__":
    display.scroll("ZSaPR")
    while True:
        led.on()
        time.sleep(0.5)
        led.off()
        time.sleep(0.5)
