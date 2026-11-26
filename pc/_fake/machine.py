# _fake/machine.py

"""
Falešný modul machine pro MicroPython na RP2040 (mpy sim, mpy test).

Simuluje hardware desky tak, aby na PC běžel main.py i knihovna
lib/picoed_v2_lib beze změny:

- Pin      digitální vstupy a výstupy, přerušení (irq)
- PWM      pulzně šířková modulace (bzučák, jas LED)
- ADC      analogové vstupy (hodnotu nastaví test: nastav_analog)
- I2C      sběrnice I2C; na Pico:ed je na sběrnici 0 displej IS31FL3731
           (adresa 0x74) - model čipu si pamatuje, co displej ukazuje
- Timer    časovače (v testu je spouští posun času, v simulaci vlákno)
- time_pulse_us, freq, reset, unique_id, WDT, Signal, ...

Simulovaná deska (nastav_desku):
- "picoed" (výchozí)  ELECFREAKS Pico:ed v2 - displej 0x74 na I2C0,
                      tlačítka A / B (GP20 / GP21, stisk = 0), LED GP25,
                      bzučák GP3
- "pico"              Raspberry Pi Pico - jen LED (GP25 / Pin("LED"))

Pomocné funkce pro testy (na desce nejsou):
- nastav_vstup(pin, uroven)   co je na pinu zvenku (0, 1, None = nic)
- stiskni(klavesa, stisknuto) tlačítko desky ("a", "b")
- nastav_analog(pin, hodnota) co vrátí ADC.read_u16()
- nastav_pulz(pin, us)        co vrátí time_pulse_us (např. ultrazvuk)
- pridej_i2c(sbernice, adresa, zarizeni)  vlastní zařízení na I2C
- historie(pin)               všechny hodnoty zapsané na výstup
- displej()                   model displeje Pico:ed (obraz(), text)
"""

import sys
import threading
import traceback

try:
    from . import _rezim                        # nacteno jako balicek _fake
    from . import adafruit_ticks as _ticks
    from . import utime as _utime
except ImportError:
    import _rezim                               # nacteno primo ze slozky _fake
    import adafruit_ticks as _ticks
    import utime as _utime


# =========================================================
# Simulovana deska
# =========================================================

class ZarizeniI2C:
    """Obecne zarizeni na I2C: 256 registru, zapis i cteni od zadaneho registru.

    Test si muze vytvorit vlastni zarizeni (senzor) a pridat ho
    funkci pridej_i2c(). Hodnoty registru jsou v .registry."""

    def __init__(self):
        self.registry = bytearray(256)
        self._ukazatel = 0

    def zapis(self, registr, data):
        for i, b in enumerate(data):
            self.registry[(registr + i) & 0xFF] = b
        self._ukazatel = (registr + len(data)) & 0xFF

    def cti(self, registr, pocet):
        if registr is None:
            registr = self._ukazatel
        data = bytes(self.registry[(registr + i) & 0xFF] for i in range(pocet))
        self._ukazatel = (registr + pocet) & 0xFF
        return data


class DisplejPicoed(ZarizeniI2C):
    """Model cipu IS31FL3731, ktery na Pico:ed ridi displej 17 x 7 LED.

    Cip ma 8 snimku (frame) po 0xB4 registrech a konfiguracni banku 0x0B.
    Ktera banka se zapisuje, urcuje registr 0xFD. Displej ukazuje snimek
    z konfiguracniho registru 0x01. Jas LED je v registrech 0x24 + adresa."""

    SIRKA = 17
    VYSKA = 7
    _BANKA = 0xFD
    _KONFIGURACE = 0x0B
    _SNIMEK = 0x01
    _JAS = 0x24

    def __init__(self):
        super().__init__()
        self.banka = 0
        self.snimky = [bytearray(0xB4) for _ in range(8)]
        self.konfigurace = bytearray(0x0D)
        self._posledni = self.obraz()

    @staticmethod
    def adresa_led(x, y):
        """Zapojeni LED na Pico:ed (stejne jako Display._pixel_addr)."""
        if x > 8:
            x = 17 - x
            y += 8
        else:
            y = 7 - y
        return x * 16 + y

    def zobrazeny_snimek(self):
        return self.konfigurace[self._SNIMEK] & 7

    def obraz(self):
        """Co displej prave ukazuje: 7 radku po 17 hodnotach jasu (0 = nesviti)."""
        snimek = self.snimky[self.zobrazeny_snimek()]
        return [[snimek[self._JAS + self.adresa_led(x, y)] for x in range(self.SIRKA)]
                for y in range(self.VYSKA)]

    def svitici(self):
        """Obraz jako text: '#' sviti, '.' nesviti (radky oddelene znakem \\n)."""
        return "\n".join("".join("#" if v else "." for v in radek) for radek in self.obraz())

    def zapis(self, registr, data):
        zmena = False
        for i, b in enumerate(data):
            r = registr + i
            if r == self._BANKA:
                self.banka = b
            elif self.banka == self._KONFIGURACE:
                if r < len(self.konfigurace):
                    self.konfigurace[r] = b
                    zmena = zmena or r == self._SNIMEK
            elif self.banka < 8 and r < 0xB4:
                self.snimky[self.banka][r] = b
                zmena = zmena or (self.banka == self.zobrazeny_snimek() and r >= self._JAS)
        if zmena:
            self._oznam_zmenu()

    def cti(self, registr, pocet):
        if registr == self._BANKA:
            return bytes([self.banka]) * pocet
        if self.banka == self._KONFIGURACE:
            pamet = self.konfigurace
        elif self.banka < 8:
            pamet = self.snimky[self.banka]
        else:
            return bytes(pocet)
        return bytes(pamet[registr + i] if registr + i < len(pamet) else 0 for i in range(pocet))

    def _oznam_zmenu(self):
        obraz = self.obraz()
        if obraz != self._posledni:
            self._posledni = obraz
            _rezim.oznam("displej", "obraz", obraz)


class _Deska:
    """Co je na simulovane desce pripojene."""

    def __init__(self, nazev):
        if nazev not in ("picoed", "pico"):
            raise ValueError(f"Neznama deska: {nazev} (picoed nebo pico)")
        self.nazev = nazev
        self.piny = {}                  # cislo GPIO -> _StavPinu
        self.i2c = {0: {}, 1: {}}       # sbernice -> {adresa: zarizeni}
        self.analog = {}                # cislo GPIO / kanal -> hodnota read_u16
        self.pulzy = {}                 # cislo GPIO -> delka pulzu v us
        self.jmena = {25: "LED"}        # jmena pinu pro konzoli simulace
        self.bzucak = None
        self.displej = None
        if nazev == "picoed":
            self.displej = DisplejPicoed()
            self.i2c[0][0x74] = self.displej
            self.jmena.update({20: "BUTTON_A", 21: "BUTTON_B", 3: "BUZZER"})
            self.bzucak = 3
            _rezim.registruj_tlacitko("a", lambda stisknuto: _tlacitko(20, stisknuto))
            _rezim.registruj_tlacitko("b", lambda stisknuto: _tlacitko(21, stisknuto))
        else:
            _rezim.registruj_tlacitko("a", None)        # Pico nema tlacitka A / B
            _rezim.registruj_tlacitko("b", None)

    def stav(self, cislo):
        if cislo not in self.piny:
            self.piny[cislo] = _StavPinu(cislo, self.jmena.get(cislo, f"GP{cislo}"))
        return self.piny[cislo]


_deska = None


def nastav_desku(nazev="picoed"):
    """Simulovana deska: "picoed" (vychozi) nebo "pico". Vse vrati do vychoziho stavu."""
    global _deska
    _planovac.zrus_vse()
    _deska = _Deska(nazev)
    _dluh_sbernice[0] = 0


def _reset():
    nastav_desku(_deska.nazev if _deska else "picoed")


_rezim.pri_resetu(_reset)


def _tlacitko(cislo, stisknuto):
    """Tlacitko na Pico:ed spoji pin se zemi: stisknuto = 0, pusteno = nic (pull-up da 1)."""
    stav = _deska.stav(cislo)
    _rezim.oznam("tlacitko", stav.jmeno, bool(stisknuto))
    stav.nastav_zvenku(0 if stisknuto else None)


# =========================================================
# Pin
# =========================================================

class _StavPinu:
    """Stav jednoho GPIO. Vic objektu Pin(25) sdili stejny stav - jako na desce."""

    def __init__(self, cislo, jmeno):
        self.cislo = cislo
        self.jmeno = jmeno
        self.rezim = Pin.IN
        self.pull = None
        self.vystup = 0
        self.zvenku = None          # co je na pin pripojene zvenku (None = nic)
        self.historie = []          # hodnoty zapsane na vystup
        self.irq_obsluha = None
        self.irq_spoustec = 0
        self.irq_pin = None
        self.irq_priznaky = 0

    def hodnota(self):
        if self.rezim == Pin.OUT:
            return self.vystup
        if self.rezim == Pin.OPEN_DRAIN and self.vystup == 0:
            return 0
        if self.zvenku is not None:
            return self.zvenku
        return 1 if self.pull == Pin.PULL_UP else 0

    def zapis(self, v):
        v = 1 if v else 0
        stara = self.hodnota()
        zmena_vystupu = v != self.vystup
        self.vystup = v
        self.historie.append(v)
        if zmena_vystupu and self.rezim in (Pin.OUT, Pin.OPEN_DRAIN):
            _rezim.oznam("pin", self.jmeno, v)
        self._preruseni(stara)

    def nastav_zvenku(self, uroven):
        stara = self.hodnota()
        self.zvenku = None if uroven is None else (1 if uroven else 0)
        self._preruseni(stara)

    def _preruseni(self, stara):
        nova = self.hodnota()
        if nova == stara or self.irq_obsluha is None:
            return
        priznak = Pin.IRQ_RISING if nova else Pin.IRQ_FALLING
        if self.irq_spoustec & priznak:
            self.irq_priznaky = priznak
            self.irq_obsluha(self.irq_pin)


class _Preruseni:
    """Objekt vraceny Pin.irq()."""

    def __init__(self, stav):
        self._stav = stav

    def flags(self):
        return self._stav.irq_priznaky

    def trigger(self, spoustec=None):
        if spoustec is None:
            return self._stav.irq_spoustec
        self._stav.irq_spoustec = spoustec
        return None


_NIC = object()


def _cislo_pinu(id):
    if isinstance(id, Pin):
        return id._stav.cislo
    if isinstance(id, int) and 0 <= id <= 29:
        return id
    if isinstance(id, str):
        jmeno = id.upper()
        if jmeno == "LED":
            return 25
        for predpona in ("GPIO", "GP"):
            if jmeno.startswith(predpona) and jmeno[len(predpona):].isdigit():
                return _cislo_pinu(int(jmeno[len(predpona):]))
    raise ValueError(f"invalid pin {id!r}")


class Pin:
    """Digitalni pin. Pin(25, Pin.OUT).value(1) rozsviti LED."""

    IN = 0
    OUT = 1
    OPEN_DRAIN = 2
    ALT = 3
    PULL_UP = 1
    PULL_DOWN = 2
    IRQ_LOW_LEVEL = 1
    IRQ_HIGH_LEVEL = 2
    IRQ_FALLING = 4
    IRQ_RISING = 8

    def __init__(self, id, mode=-1, pull=-1, *, value=None, alt=-1):
        self._stav = _deska.stav(_cislo_pinu(id))
        self.init(mode, pull, value=value)

    def init(self, mode=-1, pull=-1, *, value=None, alt=-1):
        if value is not None:
            self._stav.vystup = 1 if value else 0
        if mode != -1 and mode is not None:
            stara = self._stav.hodnota()
            self._stav.rezim = mode
            if mode == Pin.OUT and self._stav.vystup:
                _rezim.oznam("pin", self._stav.jmeno, 1)
            self._stav._preruseni(stara)
        if pull != -1:
            self._stav.pull = pull

    def value(self, x=None):
        if x is None:
            return self._stav.hodnota()
        self._stav.zapis(x)
        return None

    __call__ = value

    def on(self):
        self._stav.zapis(1)

    def off(self):
        self._stav.zapis(0)

    high = on
    low = off

    def toggle(self):
        self._stav.zapis(not self._stav.vystup)

    def mode(self, mode=None):
        if mode is None:
            return self._stav.rezim
        self.init(mode)
        return None

    def pull(self, pull=None):
        if pull is None:
            return self._stav.pull
        self._stav.pull = pull
        return None

    def irq(self, handler=_NIC, trigger=_NIC, hard=False):
        """Preruseni pri zmene pinu. Bez parametru jen vrati objekt preruseni."""
        if handler is not _NIC or trigger is not _NIC:
            self._stav.irq_obsluha = None if handler is _NIC else handler
            self._stav.irq_spoustec = (Pin.IRQ_FALLING | Pin.IRQ_RISING) if trigger is _NIC else trigger
            self._stav.irq_pin = self
        return _Preruseni(self._stav)

    def __repr__(self):
        rezim = {0: "IN", 1: "OUT", 2: "OPEN_DRAIN", 3: "ALT"}.get(self._stav.rezim, "?")
        return f"Pin(GPIO{self._stav.cislo}, mode={rezim})"


class Signal:
    """Pin s moznosti obratit logiku (invert=True: on() da na pin 0)."""

    def __init__(self, pin, *args, invert=False, **kwargs):
        self._pin = pin if isinstance(pin, Pin) else Pin(pin, *args, **kwargs)
        self._invert = invert

    def value(self, x=None):
        if x is None:
            return self._pin.value() ^ self._invert
        self._pin.value(bool(x) ^ self._invert)
        return None

    def on(self):
        self.value(1)

    def off(self):
        self.value(0)


# =========================================================
# PWM a ADC
# =========================================================

class PWM:
    """PWM na pinu. Na bzucaku Pico:ed (GP3) je to ton: freq = vyska, duty > 0 = zni."""

    def __init__(self, pin, *, freq=None, duty_u16=None, duty_ns=None, invert=False):
        self._stav = _deska.stav(_cislo_pinu(pin))
        self._freq = 0
        self._duty = 0
        self._posledni = (0, 0)
        self.historie = []          # (freq, duty_u16) po kazde zmene
        self.init(freq=freq, duty_u16=duty_u16, duty_ns=duty_ns)

    def init(self, *, freq=None, duty_u16=None, duty_ns=None, invert=False):
        if freq is not None:
            self._freq = int(freq)
        if duty_u16 is not None:
            self._duty = int(duty_u16)
        if duty_ns is not None and self._freq:
            self._duty = int(duty_ns * self._freq * 65535 // 1_000_000_000)
        self._zmena()

    def freq(self, hodnota=None):
        if hodnota is None:
            return self._freq
        self._freq = int(hodnota)
        self._zmena()
        return None

    def duty_u16(self, hodnota=None):
        if hodnota is None:
            return self._duty
        self._duty = max(0, min(65535, int(hodnota)))
        self._zmena()
        return None

    def duty_ns(self, hodnota=None):
        if hodnota is None:
            return self._duty * 1_000_000_000 // (self._freq * 65535) if self._freq else 0
        if self._freq:
            self._duty = max(0, min(65535, int(hodnota * self._freq * 65535 // 1_000_000_000)))
        self._zmena()
        return None

    def deinit(self):
        self._duty = 0
        self._zmena()

    def _zmena(self):
        stav = (self._freq, self._duty)
        if stav == self._posledni:
            return
        posledni_ton = self._posledni[0] if self._posledni[1] else 0
        self._posledni = stav
        self.historie.append(stav)
        if self._stav.cislo == _deska.bzucak:
            ton = self._freq if self._duty else 0
            if ton != posledni_ton:
                if ton:
                    _rezim.oznam("bzucak", "pitch", (ton, None))
                else:
                    _rezim.oznam("bzucak", "stop", None)
        else:
            _rezim.oznam("pwm", self._stav.jmeno, stav)


class ADC:
    """Analogovy vstup (GP26-GP29 = kanal 0-3, kanal 4 = teplota cipu)."""

    CORE_TEMP = 4

    def __init__(self, pin, *args, **kwargs):
        if isinstance(pin, int) and 0 <= pin <= 4:
            self._kanal = pin + 26 if pin < 4 else 4
        else:
            self._kanal = _cislo_pinu(pin)

    def read_u16(self):
        vychozi = 14_000 if self._kanal == 4 else 0     # teplota ~ 27 C
        return _deska.analog.get(self._kanal, vychozi)

    def read_uv(self):
        return self.read_u16() * 3_300_000 // 65535


# =========================================================
# I2C
# =========================================================

# Cas, ktery prenos po sbernici zabere (napr. rolovani textu na displeji
# trva na desce znatelnou dobu). Kratke useky se scitaji a ceka se az po 2 ms.
_dluh_sbernice = [0]


def _cas_prenosu(bajtu, frekvence):
    us = (bajtu + 1) * 9 * 1_000_000 // max(1, frekvence) + 10
    _dluh_sbernice[0] += us
    if _dluh_sbernice[0] >= 2000:
        cekej, _dluh_sbernice[0] = _dluh_sbernice[0], 0
        _utime.sleep_us(cekej)


class I2C:
    """Sbernice I2C. scan() vrati adresy zarizeni (Pico:ed: [0x74] na sbernici 0)."""

    def __init__(self, id=0, *, scl=None, sda=None, freq=400_000, timeout=50_000):
        self._id = id
        self._freq = freq

    def init(self, *, scl=None, sda=None, freq=400_000, timeout=50_000):
        self._freq = freq

    def deinit(self):
        pass

    def scan(self):
        return sorted(_deska.i2c.get(self._id, {}))

    def _zarizeni(self, adresa):
        zarizeni = _deska.i2c.get(self._id, {}).get(adresa)
        if zarizeni is None:
            raise OSError(5, "EIO")     # jako na desce: nikdo neodpovedel
        return zarizeni

    def writeto(self, addr, buf, stop=True):
        data = bytes(buf)
        zarizeni = self._zarizeni(addr)
        _cas_prenosu(len(data), self._freq)
        if data:
            zarizeni.zapis(data[0], data[1:])
        return len(data)

    def writevto(self, addr, vector, stop=True):
        return self.writeto(addr, b"".join(bytes(b) for b in vector), stop)

    def readfrom(self, addr, nbytes, stop=True):
        zarizeni = self._zarizeni(addr)
        _cas_prenosu(nbytes, self._freq)
        return zarizeni.cti(None, nbytes)

    def readfrom_into(self, addr, buf, stop=True):
        buf[:] = self.readfrom(addr, len(buf), stop)

    def writeto_mem(self, addr, memaddr, buf, *, addrsize=8):
        zarizeni = self._zarizeni(addr)
        _cas_prenosu(len(buf) + 1, self._freq)
        zarizeni.zapis(memaddr, bytes(buf))

    def readfrom_mem(self, addr, memaddr, nbytes, *, addrsize=8):
        zarizeni = self._zarizeni(addr)
        _cas_prenosu(nbytes + 2, self._freq)
        return zarizeni.cti(memaddr, nbytes)

    def readfrom_mem_into(self, addr, memaddr, buf, *, addrsize=8):
        buf[:] = self.readfrom_mem(addr, memaddr, len(buf), addrsize=addrsize)


class SoftI2C(I2C):
    def __init__(self, scl=None, sda=None, *, freq=400_000, timeout=50_000):
        super().__init__(0, scl=scl, sda=sda, freq=freq, timeout=timeout)


# =========================================================
# Timer
# =========================================================

class _Planovac:
    """Spousti casovace Timer.

    test: casovace spusti posun casu (time.sleep -> adafruit_ticks.advance_ticks)
    sim:  vlakno, ktere ceka na nejblizsi casovac (jako preruseni na desce
          bezi obsluha casovace "mezi" prikazy hlavniho programu)"""

    def __init__(self):
        self._casovace = []
        self._podminka = threading.Condition()
        self._vlakno = None

    def pridej(self, casovac):
        with self._podminka:
            if casovac not in self._casovace:
                self._casovace.append(casovac)
            self._podminka.notify()
        if _rezim.je_simulace() and self._vlakno is None:
            self._vlakno = threading.Thread(target=self._smycka, name="machine.Timer", daemon=True)
            self._vlakno.start()

    def odeber(self, casovac):
        with self._podminka:
            if casovac in self._casovace:
                self._casovace.remove(casovac)
            self._podminka.notify()

    def zrus_vse(self):
        with self._podminka:
            self._casovace.clear()
            self._podminka.notify()

    def _nejblizsi(self):
        return min(self._casovace, key=lambda c: c._termin) if self._casovace else None

    def _vyprsel(self, casovac):
        """Casovac vyprsel: periodicky naplanuje znovu, jednorazovy odebere."""
        if casovac._mode == Timer.PERIODIC:
            casovac._termin += casovac._perioda
        elif casovac in self._casovace:
            self._casovace.remove(casovac)

    def dobehni(self, cil_ms):
        """Test: spusti vsechny casovace, ktere vyprsi do casu cil_ms (po poradi)."""
        while True:
            with self._podminka:
                casovac = self._nejblizsi()
                if casovac is None or casovac._termin > cil_ms:
                    return
                termin = casovac._termin
                self._vyprsel(casovac)
            _ticks.set_ticks_ms(int(termin))
            casovac._spust()

    def _smycka(self):
        while True:
            with self._podminka:
                casovac = self._nejblizsi()
                if casovac is None:
                    self._podminka.wait()
                    continue
                zbyva = casovac._termin - _ticks.ticks_ms()
                if zbyva > 0:
                    self._podminka.wait(min(zbyva / 1000, 0.5))
                    continue
                self._vyprsel(casovac)
            casovac._spust()


_planovac = _Planovac()
_rezim.casovace = _planovac.dobehni


class Timer:
    """Casovac: Timer(period=500, mode=Timer.PERIODIC, callback=funkce)."""

    ONE_SHOT = 0
    PERIODIC = 1

    def __init__(self, id=-1, **kwargs):
        self._mode = Timer.PERIODIC
        self._perioda = 0
        self._termin = 0
        self._callback = None
        if kwargs:
            self.init(**kwargs)

    def init(self, *, mode=PERIODIC, period=-1, freq=-1, callback=None, tick_hz=1000):
        if freq is not None and freq > 0:
            perioda = 1000 / freq
        elif period is not None and period >= 0:
            perioda = period * 1000 / tick_hz
        else:
            raise ValueError("Timer.init: zadej period (ms) nebo freq (Hz)")
        _planovac.odeber(self)
        self._mode = mode
        self._perioda = max(perioda, 0.001)
        self._callback = callback
        self._termin = _ticks.ticks_ms() + self._perioda
        _planovac.pridej(self)

    def deinit(self):
        _planovac.odeber(self)

    def _spust(self):
        if self._callback is None:
            return
        if not _rezim.je_simulace():
            self._callback(self)            # v testu chyba v obsluze shodi test
            return
        try:
            self._callback(self)
        except Exception:
            self.deinit()
            print("Chyba v obsluze casovace (Timer callback) - casovac zastaven:", file=sys.stderr)
            traceback.print_exc()


# =========================================================
# Ostatni funkce modulu machine
# =========================================================

def time_pulse_us(pin, pulse_level, timeout_us=1_000_000):
    """Delka pulzu na pinu v us. Bez pulzu (nastav_pulz) ceka timeout_us a vrati -2."""
    delka = _deska.pulzy.get(_cislo_pinu(pin))
    if delka is None:
        _utime.sleep_us(timeout_us)
        return -2
    _utime.sleep_us(delka)
    return delka


def freq(hz=None):
    return 125_000_000 if hz is None else None


def unique_id():
    return b"PC-SIMUL"


def idle():
    pass


def lightsleep(ms=None):
    if ms is not None:
        _utime.sleep_ms(ms)


def deepsleep(ms=None):
    print("machine.deepsleep() - deska by usnula, simulace konci.")
    raise SystemExit(0)


def reset():
    print("machine.reset() - deska by se restartovala, simulace konci.")
    raise SystemExit(0)


soft_reset = reset


def bootloader(*args):
    print("machine.bootloader() - deska by se prepnula do BOOTSEL, simulace konci.")
    raise SystemExit(0)


def disable_irq():
    return 0


def enable_irq(stav=0):
    pass


def reset_cause():
    return PWRON_RESET


PWRON_RESET = 1
WDT_RESET = 3


class WDT:
    """Hlidaci pes. Na PC neresetuje - feed() nic nedela."""

    def __init__(self, id=0, timeout=5000):
        pass

    def feed(self):
        pass


def __getattr__(jmeno):
    raise AttributeError(f"machine.{jmeno} se na PC nesimuluje (pc/_fake/machine.py)")


# =========================================================
# Pomocne funkce pro testy
# =========================================================

def nastav_vstup(pin, uroven):
    """Co je na pinu pripojene zvenku: 0, 1 nebo None (nic - plati pull-up / pull-down)."""
    _deska.stav(_cislo_pinu(pin)).nastav_zvenku(uroven)


def stiskni(klavesa, stisknuto=True):
    """Stiskne / pusti tlacitko desky: stiskni("a"), stiskni("a", False)."""
    if not _rezim.stiskni(klavesa, stisknuto):
        raise ValueError(f"Deska {_deska.nazev} nema tlacitko {klavesa!r}")


def nastav_analog(pin, hodnota):
    """Hodnota, kterou vrati ADC(pin).read_u16() (0-65535)."""
    kanal = ADC(pin)._kanal
    _deska.analog[kanal] = int(hodnota)


def nastav_pulz(pin, us):
    """Delka pulzu, kterou vrati time_pulse_us(pin, ...); None = zadny pulz."""
    cislo = _cislo_pinu(pin)
    if us is None:
        _deska.pulzy.pop(cislo, None)
    else:
        _deska.pulzy[cislo] = int(us)


def pridej_i2c(sbernice, adresa, zarizeni=None):
    """Pripoji zarizeni na I2C (vychozi: ZarizeniI2C s 256 registry) a vrati ho."""
    if zarizeni is None:
        zarizeni = ZarizeniI2C()
    _deska.i2c.setdefault(sbernice, {})[adresa] = zarizeni
    return zarizeni


def historie(pin):
    """Vsechny hodnoty zapsane na vystup pinu (napr. [1, 0, 1, 0])."""
    return list(_deska.stav(_cislo_pinu(pin)).historie)


def displej():
    """Model displeje Pico:ed (None na desce bez displeje)."""
    return _deska.displej


nastav_desku("picoed")
