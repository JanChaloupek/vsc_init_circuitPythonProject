# _fake/micropython.py

"""
Falešný modul micropython (mpy sim, mpy test).

Na desce slouží k optimalizacím a ladění paměti. Na PC nic z toho
není potřeba - funkce jen vrátí, co dostaly, nebo nic nedělají.
"""


def const(hodnota):
    """const(5) je na desce konstanta prekladace, na PC jen hodnota."""
    return hodnota


def native(funkce):
    """Dekorator @micropython.native - na PC nic nemeni."""
    return funkce


viper = native
asm_thumb = native


def schedule(funkce, argument):
    """Na desce naplanuje funkci z preruseni do hlavniho programu, na PC ji hned zavola."""
    funkce(argument)


def alloc_emergency_exception_buf(velikost):
    pass


def opt_level(uroven=None):
    return 0 if uroven is None else None


def mem_info(podrobne=False):
    print("mem: (na PC se pamet desky nesleduje)")


def qstr_info(podrobne=False):
    print("qstr: (na PC se nesleduje)")


def stack_use():
    return 0


def heap_lock():
    return 0


def heap_unlock():
    return 0


def heap_locked():
    return 0


def kbd_intr(znak):
    pass
