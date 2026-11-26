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

Vystup je zamerne jen ASCII: konzole Windows (cp1250) neumi vsechny znaky.
"""

import _thread
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
    if co in ("neopixel", "displej") and kdo != "scroll":
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
            _vypis(f"Bzucak: ton {frekvence} Hz" + (f", {delka} ms" if delka else ""))
        elif kdo == "play":
            _vypis(f"Bzucak: melodie {hodnota!r}")
        else:
            _vypis("Bzucak: ticho")
    elif co == "tlacitko":
        jmeno = _JMENA_TLACITEK.get(kdo, kdo)
        _vypis(f"Tlacitko {jmeno}: " + ("stisknuto" if hodnota else "pusteno"))
    elif co == "neopixel":
        _vypis("NeoPixel: " + " ".join("#%02x%02x%02x" % tuple(p[:3]) for p in hodnota))


# ---------------------------------------------------------
# Klavesy
# ---------------------------------------------------------

def _stiskni(jmeno):
    picoed = sys.modules.get("picoed")
    tlacitko = getattr(picoed, jmeno, None)
    if tlacitko is None:
        return
    tlacitko.set_pressed(True)
    casovac = threading.Timer(DRZENI_TLACITKA, tlacitko.set_pressed, args=(False,))
    casovac.daemon = True
    casovac.start()


def _klavesa(znak):
    znak = znak.lower()
    if znak == "a":
        _stiskni("button_a")
    elif znak == "b":
        _stiskni("button_b")
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
    while _bezi:
        pripraveno, _, _ = select.select([sys.stdin], [], [], 0.05)
        if pripraveno:
            _klavesa(sys.stdin.read(1))


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
