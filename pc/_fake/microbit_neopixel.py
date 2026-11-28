# _fake/microbit_neopixel.py

"""
Falešný modul neopixel pro BBC micro:bit (mpy sim, mpy test - deska "microbit").

V programu se importuje jako `import neopixel` / `from neopixel import NeoPixel`:

    np = NeoPixel(pin16, 4)
    np[0] = (255, 0, 0)
    np.show()

Barvy se oznámí až při show() (konzole: NeoPixel: #ff0000 #000000 ...).
Pro testy (na desce není): np.historie - seznam stavů po každém show().
"""

try:
    from . import _rezim
except ImportError:
    import _rezim


class NeoPixel:
    """Pasek / kruh barevnych LED na pinu."""

    def __init__(self, pin, n, bpp=3):
        if bpp not in (3, 4):
            raise ValueError("bpp must be 3 or 4")
        self.n = int(n)
        self._bpp = bpp
        self._jmeno = getattr(pin, "_jmeno", str(pin))
        self._pixely = [(0,) * bpp for _ in range(self.n)]
        self.historie = []          # jen na PC: stav po kazdem show()

    def __len__(self):
        return self.n

    def __getitem__(self, i):
        return self._pixely[i]

    def __setitem__(self, i, barva):
        barva = tuple(int(v) for v in barva)
        if len(barva) != self._bpp or not all(0 <= v <= 255 for v in barva):
            raise ValueError("colour must be a tuple of %d values 0-255" % self._bpp)
        self._pixely[i] = barva

    def fill(self, barva):
        for i in range(self.n):
            self[i] = barva

    def clear(self):
        """Zhasne vsechny LED (hned, bez show())."""
        self._pixely = [(0,) * self._bpp for _ in range(self.n)]
        self.show()

    def show(self):
        stav = list(self._pixely)
        self.historie.append(stav)
        _rezim.oznam("neopixel", self._jmeno, stav)

    write = show
