# code.py - Vychozi starter program pro CircuitPython
# Cilove desky v projektu:
#   - ELECFREAKS Pico:ed verze 1 (RP2040, 17x7 LED matice, bzucak GP0)
#   - ELECFREAKS Pico:ed verze 2 (RP2040, 17x7 LED matice, bzucak GP3)
#
# Popis:
#   CircuitPython je v projektu vyhrazen pro desky Pico:ed v1 a v2.
#   Tento skript vyuziva vestaveny modul picoed a blika stavovou LED.

import time

# Zkusime nativni modul picoed pro desky Pico:ed v1 a v2
try:
    import picoed
    led = picoed.led
    display = getattr(picoed, "display", None)
    board_name = "ELECFREAKS Pico:ed (v1 / v2)"
except (ImportError, AttributeError):
    # Deska s CircuitPythonem bez modulu picoed (napr. Raspberry Pi Pico):
    # LED pres modul board. (Simulace na PC - cpy sim - pouziva falesny
    # picoed z pc/_fake, takze bezi vetev vyse.)
    try:
        import board
        import digitalio
        pin = getattr(board, "LED", None) or getattr(board, "GP25", None)
        led_io = digitalio.DigitalInOut(pin)
        led_io.direction = digitalio.Direction.OUTPUT

        class _FallbackLed:
            def on(self): led_io.value = True
            def off(self): led_io.value = False
            def toggle(self): led_io.value = not led_io.value

        led = _FallbackLed()
        display = None
        board_name = "CircuitPython deska (board.LED)"
    except Exception:
        class _ConsoleLed:
            _s = False
            def on(self): self._s = True; print("[LED] ON")
            def off(self): self._s = False; print("[LED] OFF")
            def toggle(self):
                if self._s: self.off()
                else: self.on()

        led = _ConsoleLed()
        display = None
        board_name = "PC / Console Simulator"

if __name__ == "__main__":
    print(f"Spusteno code.py (CircuitPython na {board_name})")

    # Pokud je dostupny displej Pico:ed, nechame po nem projet uvodni text
    if display:
        try:
            display.scroll("ZSaPR")
        except Exception:
            pass

    # Pravidelne blikani stavove LED (interval 1 s)
    while True:
        led.toggle()
        time.sleep(1)
