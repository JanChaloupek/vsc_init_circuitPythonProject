# main.py - Vychozi starter program pro MicroPython
# Podporovane platformy v projektu:
#   - Raspberry Pi Pico / Pico W
#   - ELECFREAKS Pico:ed v2
#   - BBC micro:bit v1 / v2

import time

display = None
led = None
board_name = "Neznama deska"

# 1. Zkusime BBC micro:bit (vestaveny modul microbit)
try:
    import microbit
    class _MicrobitDisplay:
        def scroll(self, text): microbit.display.scroll(text)
        def show(self, val): microbit.display.show(val)

    class _MicrobitLed:
        def on(self): microbit.display.set_pixel(2, 2, 9)
        def off(self): microbit.display.set_pixel(2, 2, 0)
        def toggle(self):
            cur = microbit.display.get_pixel(2, 2)
            microbit.display.set_pixel(2, 2, 0 if cur > 0 else 9)

    display = _MicrobitDisplay()
    led = _MicrobitLed()
    board_name = "BBC micro:bit"
except (ImportError, Exception):
    pass

# 2. Zkusime ELECFREAKS Pico:ed v2
# (Pico:ed ma na I2C sbernici 0 displej IS31FL3731 na adrese 0x74)
if display is None:
    try:
        from machine import I2C, Pin
        from picoed_v2_lib.iic import IIC
        from picoed_v2_lib import Display, Led
        i2c = I2C(IIC.BUS0, sda=Pin(IIC.SDA0), scl=Pin(IIC.SCL0))
        if 0x74 in i2c.scan():
            display = Display(i2c)
            led = Led()
            board_name = "ELECFREAKS Pico:ed v2"
    except Exception:
        pass

# 3. Zkusime Raspberry Pi Pico / Pico W (modul machine)
if display is None:
    try:
        from machine import Pin
        try:
            # Pico i Pico W v modernim MicroPythonu
            _pin = Pin("LED", Pin.OUT)
        except Exception:
            # Starsi MicroPython na Pico
            _pin = Pin(25, Pin.OUT)

        class _PicoDisplay:
            def scroll(self, text): print(f"[Display] {text}")
            def show(self, val): print(f"[Display] {val}")

        class _PicoLed:
            def on(self): _pin.value(1)
            def off(self): _pin.value(0)
            def toggle(self): _pin.value(not _pin.value())

        display = _PicoDisplay()
        led = _PicoLed()
        board_name = "Raspberry Pi Pico"
    except Exception:
        pass

# 4. Fallback pro PC simulaci
if display is None:
    class _ConsoleDisplay:
        def scroll(self, text): print(f"[Display] {text}")
        def show(self, val): print(f"[Display] {val}")

    class _ConsoleLed:
        _s = False
        def on(self): self._s = True; print("[LED] ON")
        def off(self): self._s = False; print("[LED] OFF")
        def toggle(self):
            if self._s: self.off()
            else: self.on()

    display = _ConsoleDisplay()
    led = _ConsoleLed()
    board_name = "PC / Simulator"

if __name__ == "__main__":
    print(f"Spusteno main.py na desce: {board_name}")
    display.scroll("ZSaPR")
    while True:
        led.on()
        time.sleep(0.5)
        led.off()
        time.sleep(0.5)
