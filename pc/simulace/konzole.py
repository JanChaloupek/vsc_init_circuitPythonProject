# pc/simulace/konzole.py

"""
Konzole simulace (cpy sim).

Posloucha zmeny falesneho hardwaru (pc/_fake, _rezim.oznam) a vypisuje je
s casem od zacatku simulace:

    [    0.00 s] Displej: text "ZSaPR"
    [    0.00 s] LED: ZAPNUTO (*)
    [    1.00 s] LED: vypnuto ( )

Klavesy (jen kdyz je vstup terminal):
    a / b  ... stisk tlacitka A / B (drzi se DRZENI_TLACITKA sekund)
    q      ... konec simulace (jako Ctrl+C)

Co klavesa udela, urcuje simulovana deska (_rezim.registruj_tlacitko):
falesny picoed (CircuitPython) i falesny machine pro Pico:ed (MicroPython).

Vystup je zamerne jen ASCII: konzole Windows (cp1250) neumi vsechny znaky.
"""

import _thread
import os
import sys
import threading

DRZENI_TLACITKA = 0.5   # jak dlouho je tlacitko "stisknute" po stisku klavesy

_rezim = None
_bezi = False
_tty_obnov = None       # funkce, ktera vrati terminal do puvodniho stavu (Linux/macOS)

_JMENA_TLACITEK = {"BUTTON_A": "A", "BUTTON_B": "B"}


# ---------------------------------------------------------
# Vypis zmen hardwaru
# ---------------------------------------------------------

def _vypis(text):
    cas = _rezim.realny_cas_ms() / 1000 if _rezim else 0.0
    print(f"[{cas:9.2f} s] {text}", flush=True)


def _obraz(radky):
    """Matice displeje 17 x 7: '#' sviti, '.' nesviti."""
    return "\n".join("               " + "".join("#" if v else "." for v in radek) for radek in radky)


# Posledni vypsany stav zarizeni, ktera program prepisuje porad dokola
# (NeoPixel.show() v kazdem cyklu) - vypisuje se jen zmena.
_posledni = {}


def _posluchac(co, kdo, hodnota):
    if co in ("neopixel", "displej", "pwm") and kdo != "scroll":
        if _posledni.get((co, kdo)) == hodnota:
            return
        _posledni[(co, kdo)] = hodnota
    if co == "pin":
        if kdo == "LED":
            _vypis("LED: " + ("ZAPNUTO (*)" if hodnota else "vypnuto ( )"))
        else:
            _vypis(f"Pin {kdo}: {int(bool(hodnota))}")
    elif co == "displej":
        if kdo == "scroll":
            _vypis(f'Displej: text "{hodnota}"')
        else:
            _vypis("Displej:\n" + _obraz(hodnota))
    elif co == "bzucak":
        if kdo == "pitch":
            frekvence, delka = hodnota
            if not frekvence:
                _vypis("Bzucak: ticho")
            else:
                _vypis(f"Bzucak: ton {frekvence} Hz" + (f", {delka:g} ms" if delka else ""))
        elif kdo == "play":
            _vypis(f"Bzucak: melodie {hodnota}" if isinstance(hodnota, str) and hodnota.startswith("Music.")
                   else f"Bzucak: melodie {hodnota!r}")
        else:
            _vypis("Bzucak: ticho")
    elif co == "tlacitko":
        jmeno = _JMENA_TLACITEK.get(kdo, kdo)
        _vypis(f"Tlacitko {jmeno}: " + ("stisknuto" if hodnota else "pusteno"))
    elif co == "pwm":
        frekvence, strida = hodnota
        _vypis(f"PWM {kdo}: {frekvence} Hz, strida {strida * 100 / 65535:.0f} %")
    elif co == "neopixel":
        _vypis("NeoPixel: " + " ".join("#%02x%02x%02x" % tuple(p[:3]) for p in hodnota))


# ---------------------------------------------------------
# Klavesy
# ---------------------------------------------------------

def _stiskni(klavesa):
    if not _rezim.stiskni(klavesa, True):
        return                          # deska takove tlacitko nema
    casovac = threading.Timer(DRZENI_TLACITKA, _rezim.stiskni, args=(klavesa, False))
    casovac.daemon = True
    casovac.start()


def _klavesa(znak):
    znak = znak.lower()
    if znak in ("a", "b"):
        _stiskni(znak)
    elif znak == "q":
        _thread.interrupt_main()        # v hlavnim vlakne vyvola KeyboardInterrupt


def _cti_klavesy_windows():
    import msvcrt
    while _bezi:
        if msvcrt.kbhit():
            _klavesa(msvcrt.getwch())
        else:
            _rezim.realne_cekej(0.05)


def _cti_klavesy_posix():
    import select
    fd = sys.stdin.fileno()
    while _bezi:
        pripraveno, _, _ = select.select([fd], [], [], 0.05)
        if pripraveno:
            # os.read misto sys.stdin.read: stdin ma vlastni vyrovnavaci pamet
            # a select by o znacich, ktere uz jsou v ni, nevedel
            for znak in os.read(fd, 32).decode(errors="ignore"):
                _klavesa(znak)


# ---------------------------------------------------------
# Start a konec
# ---------------------------------------------------------

def spust(rezim):
    """Zacne vypisovat zmeny hardwaru a cist klavesy. Vrati True, kdyz
    klavesy funguji (vstup je terminal)."""
    global _rezim, _bezi, _tty_obnov
    _rezim = rezim
    _bezi = True
    rezim.poslouchej(_posluchac)
    if not sys.stdin.isatty():
        return False
    if sys.platform == "win32":
        cteni = _cti_klavesy_windows
    else:
        import termios
        import tty
        fd = sys.stdin.fileno()
        puvodni = termios.tcgetattr(fd)
        tty.setcbreak(fd)               # znaky hned, bez Enteru
        _tty_obnov = lambda: termios.tcsetattr(fd, termios.TCSADRAIN, puvodni)
        cteni = _cti_klavesy_posix
    threading.Thread(target=cteni, daemon=True).start()
    return True


def zastav():
    global _bezi, _tty_obnov
    _bezi = False
    if _rezim:
        _rezim.prestan_poslouchat(_posluchac)
    if _tty_obnov:
        _tty_obnov()
        _tty_obnov = None
