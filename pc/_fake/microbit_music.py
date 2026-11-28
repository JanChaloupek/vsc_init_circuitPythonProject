# _fake/microbit_music.py

"""
Falešný modul music pro BBC micro:bit (mpy sim, mpy test - deska "microbit").

V programu se importuje jako `import music`:

    music.play(music.NYAN)
    music.play(["c4:4", "e", "g", "c5:8"])
    music.pitch(440, 500)

Nota je "JMENO[#|b][OKTAVA][:DELKA]", např. "c4:4", "eb:8", "r:2" (r = pauza).
Oktáva a délka platí i pro další noty, dokud se nezmění. Délka je v dobách
(ticks); doba trvá 60000 / bpm / ticks ms - výchozí tempo (4, 120) = 125 ms.

Melodie se jen oznámí (konzole: Bzucak: melodie music.NYAN) a program počká,
jak dlouho by hrála (wait=True). Vestavěné melodie mají jména jako na desce,
noty jsou přepsané z MicroPythonu pro micro:bit - délka v simulaci odpovídá
přibližně.

Pro testy (na desce není): music.historie - seznam volání
("play", noty), ("pitch", frekvence, delka), ("stop",).
"""

import re

try:
    from . import _rezim
    from . import utime as _utime
except ImportError:
    import _rezim
    import utime as _utime


DADADADUM = ("r4:2", "g", "g", "g", "eb:8", "r:2", "f", "f", "f", "d:8")
ENTERTAINER = ("d4:1", "d#", "e", "c5:2", "e4:1", "c5:2", "e4:1", "c5:3", "c:1", "d", "d#", "e",
               "c", "d", "e:2", "b4:1", "d5:2", "c:4")
PRELUDE = ("c4:1", "e", "g", "c5", "e", "g4", "c5", "e", "c4", "e", "g", "c5", "e", "g4", "c5", "e",
           "c4", "d", "a", "d5", "f", "a4", "d5", "f", "c4", "d", "a", "d5", "f", "a4", "d5", "f",
           "b3", "d4", "g", "d5", "f", "g4", "d5", "f", "b3", "d4", "g", "d5", "f", "g4", "d5", "f",
           "c4", "e", "g", "c5", "e", "g4", "c5", "e", "c4", "e", "g", "c5", "e", "g4", "c5", "e")
ODE = ("e4", "e", "f", "g", "g", "f", "e", "d", "c", "c", "d", "e", "e:6", "d:2", "d:8",
       "e:4", "e", "f", "g", "g", "f", "e", "d", "c", "c", "d", "e", "d:6", "c:2", "c:8")
NYAN = ("f#5:2", "g#", "c#:1", "d#:2", "b4:1", "d5:1", "c#", "b4:2", "b", "c#5", "d", "d:1", "c#",
        "b4:1", "c#5:1", "d#", "f#", "g#", "d#", "f#", "c#", "d", "b4", "c#5", "b4", "d#5:2", "f#",
        "g#:1", "d#", "f#", "c#", "d#", "b4", "d5", "d#", "d", "c#", "b4", "c#5", "d:2", "b4:1",
        "c#5", "d#", "f#", "c#", "d", "c#", "b4", "c#5:2", "b4", "c#5", "b4", "f#:1", "g#", "b:2",
        "f#:1", "g#", "b", "c#5", "d#", "b4", "e5", "d#", "e", "f#", "b4:2", "b", "f#:1", "g#", "b",
        "f#", "e5", "d#", "c#", "b4", "f#", "d#", "e", "f#", "b:2", "f#:1", "g#", "b:2", "f#:1",
        "g#", "b", "b", "c#5", "d#", "b4", "f#", "g#", "f#", "b:2", "b:1", "a#", "b", "f#", "g#",
        "b", "e5", "d#", "e", "f#", "b4:2", "c#5")
RINGTONE = ("c4:1", "d", "e:2", "g", "d:1", "e", "f:2", "a", "e:1", "f", "g:2", "b", "c5:4")
FUNK = ("c2:2", "c", "d#", "c:1", "f:2", "c:1", "f:2", "f#", "g", "c", "c", "g", "c:1", "f#:2",
        "c:1", "f#:2", "f", "d#")
BLUES = ("c2:2", "e", "g", "a", "a#", "a", "g", "e", "c2:2", "e", "g", "a", "a#", "a", "g", "e",
         "f", "a", "c3", "d", "d#", "d", "c", "a2", "c2:2", "e", "g", "a", "a#", "a", "g", "e",
         "g", "b", "d3", "f", "f2", "a", "c3", "d#", "c2:2", "e", "g", "e", "g", "f", "e", "d")
BIRTHDAY = ("c4:3", "c:1", "d:4", "c:4", "f", "e:8", "c:3", "c:1", "d:4", "c:4", "g", "f:8",
            "c:3", "c:1", "c5:4", "a4", "f", "e", "d", "a#:3", "a#:1", "a:4", "f", "g", "f:8")
WEDDING = ("c4:4", "f:3", "f:1", "f:8", "c:4", "g:3", "e:1", "f:8", "c:4", "f:3", "a:1", "c5:4",
           "a4:3", "f:1", "f:4", "e:3", "f:1", "g:8")
FUNERAL = ("c3:4", "c:3", "c:1", "c:4", "d#:3", "d:1", "d:3", "c:1", "c:3", "b2:1", "c3:4")
PUNCHLINE = ("c4:3", "g3:1", "f#", "g", "g#:3", "g", "r", "b", "c4")
PYTHON = ("d5:1", "b4", "r", "b", "b", "a#", "b", "g5", "r", "d", "d", "r", "b4", "c5", "r", "c",
          "c", "r", "d", "e:5", "c:1", "a4", "r", "a", "a", "g#", "a", "f#5", "r", "e", "e", "r",
          "c", "b4", "r", "b", "b", "r", "c5", "d:5", "d:1", "b4", "r", "b", "b", "a#", "b", "b5",
          "r", "g", "g", "r", "d", "c#", "r", "a", "a", "r", "a", "a:5", "g:1", "f#:2", "a:1", "a",
          "g#", "a", "e:2", "a:1", "a", "g#", "a", "d", "r", "c#", "d", "r", "c#", "d:2", "r:3")
BADDY = ("c3:3", "r", "d:2", "d#", "r", "c", "r", "f#:8")
CHASE = ("a4:1", "b", "c5", "b4", "a:2", "r", "a:1", "b", "c5", "b4", "a:2", "r", "a:2", "e5",
         "d#", "e", "f", "e", "d#", "e", "b4:1", "c5", "d", "c", "b4:2", "r", "b:1", "c5", "d",
         "c", "b4:2", "r", "b:2", "e5", "d#", "e", "f", "e", "d#", "e")
BA_DING = ("b5:1", "e6:3")
WAWAWAWAA = ("e3:3", "r:1", "d#:3", "r:1", "d:4", "r:1", "c#:8")
JUMP_UP = ("c5:1", "d", "e", "f", "g")
JUMP_DOWN = ("g5:1", "f", "e", "d", "c")
POWER_UP = ("g4:1", "c5", "e", "g:2", "e:1", "g:3")
POWER_DOWN = ("g5:1", "d#", "c", "g4:2", "b:1", "c5:3")

_NOTA = re.compile(r"^([a-gr])([#b]?)(\d*)(?::(\d+))?$", re.IGNORECASE)

_tempo = {"ticks": 4, "bpm": 120}
_posledni = {"oktava": 4, "delka": 4}       # plati pro dalsi noty, dokud se nezmeni
historie = []                               # jen na PC: co program hral (pro testy)


def _delka_ms(noty):
    """Jak dlouho noty hraji (a zapamatuje si posledni oktavu a delku)."""
    doby = 0
    for nota in noty:
        m = _NOTA.match(str(nota).strip())
        if not m:
            continue                        # deska neznamou notu taky preskoci
        if m.group(3):
            _posledni["oktava"] = int(m.group(3))
        if m.group(4):
            _posledni["delka"] = int(m.group(4))
        doby += _posledni["delka"]
    return doby * 60_000 // (_tempo["bpm"] * _tempo["ticks"])


def _jmeno(melodie):
    for jmeno, hodnota in globals().items():
        if hodnota is melodie and jmeno.isupper():
            return "music." + jmeno
    return None


def play(music, pin=None, wait=True, loop=False):
    """Zahraje melodii (seznam not nebo jedna nota jako text)."""
    noty = (music,) if isinstance(music, str) else tuple(music)
    ms = _delka_ms(noty)
    historie.append(("play", noty))
    _rezim.oznam("bzucak", "play", _jmeno(music) or list(noty))
    if not wait:
        return
    if loop:
        if _rezim.je_simulace():            # na desce by hrala navzdy
            while True:
                _rezim.realne_cekej(max(ms, 10) / 1000)
        return
    _utime.sleep_ms(ms)


def pitch(frequency, duration=-1, pin=None, wait=True):
    """Ton o frekvenci frequency Hz; duration v ms (-1 = dokud ho nezastavi stop())."""
    frequency, duration = int(frequency), int(duration)
    historie.append(("pitch", frequency, duration))
    _rezim.oznam("bzucak", "pitch", (frequency, duration if duration >= 0 else None))
    if duration >= 0 and wait:
        _utime.sleep_ms(duration)


def stop(pin=None):
    historie.append(("stop",))
    _rezim.oznam("bzucak", "stop", None)


def set_tempo(ticks=None, bpm=None):
    """Tempo: ticks = dob na ctvrtovou notu, bpm = ctvrtovych not za minutu."""
    if ticks is not None:
        _tempo["ticks"] = int(ticks)
    if bpm is not None:
        _tempo["bpm"] = int(bpm)


def get_tempo():
    return (_tempo["ticks"], _tempo["bpm"])


def reset():
    """Vychozi tempo (4, 120), oktava 4 a delka 4."""
    _tempo.update(ticks=4, bpm=120)
    _posledni.update(oktava=4, delka=4)


def _reset():
    reset()
    historie.clear()


_rezim.pri_resetu(_reset)
