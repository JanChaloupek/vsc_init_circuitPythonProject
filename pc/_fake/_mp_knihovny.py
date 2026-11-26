# _fake/_mp_knihovny.py

"""
Oznamování pro knihovnu lib/picoed_v2_lib (mpy sim, mpy test).

Knihovna běží na PC beze změny nad falešným modulem machine. Hardware ale
vidí jen nízkoúrovňové zápisy: rolování textu jsou stovky zápisů do čipu
displeje, melodie jsou desítky změn PWM. Konzole simulace by je vypsala
všechny. Proto se metody Display.scroll / clear a Music.play / pitch
obalí: oznámí se jen to podstatné ("Displej: text ZSaPR", "melodie ODE")
a dílčí změny uvnitř se neoznamují (_rezim.ticho).

Kód knihovny se nemění - obal jen přidá oznámení kolem původní metody.
"""

try:
    from . import _rezim
    from . import machine as _machine
except ImportError:
    import _rezim
    import machine as _machine


def _oznam_obraz():
    displej = _machine.displej()
    if displej is not None:
        _rezim.oznam("displej", "obraz", displej.obraz())


def _obal_displej(Display):
    puvodni_init = Display.__init__
    puvodni_scroll = Display.scroll
    puvodni_clear = Display.clear

    def __init__(self, *args, **kwargs):
        with _rezim.ticho():                # inicializace cipu - nic k vypsani
            puvodni_init(self, *args, **kwargs)

    def scroll(self, value, brightness=30):
        _rezim.oznam("displej", "scroll", str(value))
        with _rezim.ticho():
            return puvodni_scroll(self, value, brightness)

    def clear(self):
        with _rezim.ticho():
            vysledek = puvodni_clear(self)
        _oznam_obraz()
        return vysledek

    Display.__init__ = __init__
    Display.scroll = scroll
    Display.clear = clear


def _obal_hudbu(Music):
    puvodni_play = Music.play
    puvodni_pitch = Music.pitch

    def jmeno_melodie(melodie):
        for jmeno, hodnota in vars(Music).items():
            if hodnota is melodie and jmeno.isupper():
                return "Music." + jmeno
        return melodie

    def play(self, music):
        _rezim.oznam("bzucak", "play", jmeno_melodie(music))
        with _rezim.ticho():
            return puvodni_play(self, music)

    def pitch(self, frequency, duration=-1):
        _rezim.oznam("bzucak", "pitch", (frequency, duration if duration >= 0 else None))
        with _rezim.ticho():
            return puvodni_pitch(self, frequency, duration)

    Music.play = play
    Music.pitch = pitch


def obal():
    """Obali tridy knihovny picoed_v2_lib (kdyz v lib/ je). Volat jednou."""
    try:
        from picoed_v2_lib import display, music
    except ImportError:
        return False
    if getattr(display.Display, "_obaleno_pro_pc", False):
        return True
    _obal_displej(display.Display)
    _obal_hudbu(music.Music)
    display.Display._obaleno_pro_pc = True
    return True
