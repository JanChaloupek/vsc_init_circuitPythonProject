# _fake/microbit_machine.py

"""
Falešný modul machine pro BBC micro:bit (mpy sim, mpy test - deska "microbit").

Na micro:bitu je machine malý: time_pulse_us (např. ultrazvukový senzor),
reset, freq, unique_id, disable_irq / enable_irq a mem8 / mem16 / mem32.
Piny, I2C a PWM jsou v modulu microbit (pin0, i2c, pin0.write_analog) -
`from machine import Pin` na micro:bitu skončí chybou, a proto i tady.

Délku pulzu nastaví test: microbit.nastav_pulz(pin2, 580).
"""

try:
    from . import utime as _utime
except ImportError:
    import utime as _utime


def time_pulse_us(pin, pulse_level, timeout_us=1_000_000):
    """Delka pulzu na pinu v us. Bez pulzu (nastav_pulz) ceka timeout_us a vrati -2."""
    delka = getattr(pin, "_pulz", None)
    if delka is None:
        _utime.sleep_us(timeout_us)
        return -2
    _utime.sleep_us(delka)
    return delka


def freq():
    return 64_000_000


def unique_id():
    return b"PC-SIMUL"


def reset():
    print("machine.reset() - deska by se restartovala, simulace konci.")
    raise SystemExit(0)


def disable_irq():
    return 0


def enable_irq(stav=0):
    pass


class _Pamet:
    """mem8 / mem16 / mem32: na PC neni co cist - vrati 0, zapis zahodi."""

    def __getitem__(self, adresa):
        return 0

    def __setitem__(self, adresa, hodnota):
        pass


mem8 = _Pamet()
mem16 = _Pamet()
mem32 = _Pamet()


def __getattr__(jmeno):
    raise AttributeError("machine.%s na micro:bitu neni (piny, I2C a PWM jsou v modulu microbit: "
                         "pin0, i2c, pin0.write_analog)" % jmeno)
