# _fake/adafruit_ticks.py

"""
Fake implementace modulu adafruit_ticks pro testy a vývoj na PC.

Simuluje monotónní časovač CircuitPythonu:
- ticks_ms() vrací řízený simulovaný čas
- ticks_add() a ticks_diff() fungují stejně jako v MicroPythonu
- v testu (_rezim "test") se čas neposouvá automaticky, testy jej řídí ručně
- v simulaci (_rezim "sim") čas běží podle skutečných hodin a
  advance_ticks() (tedy i time.sleep) opravdu čeká
"""

try:
    from . import _rezim        # nacteno jako balicek _fake (cpy test / cpy sim / run_test.py)
except ImportError:
    import _rezim               # nacteno primo ze slozky _fake

# Konstanty převzaté z MicroPythonu
_TICKS_PERIOD = 1 << 29
_TICKS_MAX = _TICKS_PERIOD - 1
_TICKS_HALFPERIOD = _TICKS_PERIOD // 2

# Interní simulovaný čas (v milisekundách)
_fake_ticks = 0
# Posun skutečného času v simulaci (set_ticks_ms v režimu "sim")
_sim_offset = 0


def ticks_ms() -> int:
    """Vrací aktuální simulovaný čas v milisekundách."""
    if _rezim.je_simulace():
        return (_rezim.realny_cas_ms() + _sim_offset) % _TICKS_PERIOD
    return _fake_ticks


def ticks_add(ticks: int, delta: int) -> int:
    """Vrací ticks + delta s bezpečným přetečením."""
    return (ticks + delta) % _TICKS_PERIOD


def ticks_diff(ticks1: int, ticks2: int) -> int:
    """Vrací rozdíl dvou tick hodnot s ošetřením přetečení."""
    diff = (ticks1 - ticks2) & _TICKS_MAX
    diff = ((diff + _TICKS_HALFPERIOD) & _TICKS_MAX) - _TICKS_HALFPERIOD
    return diff


def ticks_less(ticks1: int, ticks2: int) -> bool:
    """Vrací True, pokud ticks1 je dříve než ticks2."""
    return ticks_diff(ticks1, ticks2) < 0


# ---------------------------------------------------------
# FakeHW rozšíření – pouze pro testy
# ---------------------------------------------------------

def set_ticks_ms(value: int) -> None:
    """Nastaví simulovaný čas v milisekundách."""
    global _fake_ticks, _sim_offset
    _fake_ticks = int(value)
    if _rezim.je_simulace():
        _sim_offset = int(value) - _rezim.realny_cas_ms()


def advance_ticks(delta: int) -> None:
    """Posune simulovaný čas o delta milisekund.

    V simulaci čas běží sám - tady se proto skutečně čeká."""
    global _fake_ticks
    if _rezim.je_simulace():
        _rezim.realne_cekej(int(delta) / 1000)
        return
    cil = _fake_ticks + int(delta)
    if _rezim.casovace is not None:
        _rezim.casovace(cil)        # casovace machine.Timer, ktere mezitim vyprsi
    _fake_ticks = cil % _TICKS_PERIOD
