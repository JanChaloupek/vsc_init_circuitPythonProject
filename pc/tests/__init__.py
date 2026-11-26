"""Unit testy, ktere bezi na PC s falesnym hardwarem z pc/_fake (cpy test).

Spousteni:  .\\cpy test            (Linux/macOS: ./cpy.sh test)
            .\\cpy test test_code*  (jen soubory odpovidajici vzoru)

Testy MicroPythonu (main.py) jsou ve slozce pc/tests_mpy (.\\mpy test).
Pred kazdym testem se simulovany cas vynuluje (adafruit_ticks.set_ticks_ms(0)).
"""
