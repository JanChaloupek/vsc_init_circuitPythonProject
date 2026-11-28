r"""Unit testy programu main.py (MicroPython), ktere bezi na PC s falesnym
hardwarem z pc/_fake (machine, utime, micropython).

Spousteni:  .\mpy test            (Linux/macOS: ./mpy.sh test)
            .\mpy test test_main*  (jen soubory odpovidajici vzoru)

Testy CircuitPythonu (code.py) jsou ve slozce pc/tests - kazda platforma
ma jine falesne moduly, a proto se spousti zvlast.
Pred kazdym testem se simulovany cas vynuluje a hardware vrati do
vychoziho stavu.

Testy bezi na simulovane desce Pico:ed v2. Test pro BBC micro:bit si
desku vybere sam (nastav_desku("microbit") v setUp) - ukazka je
v test_main_py_microbit.py. Pred dalsim testem se deska vrati na Pico:ed.
"""
