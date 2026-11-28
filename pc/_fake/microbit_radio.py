# _fake/microbit_radio.py

"""
Falešný modul radio pro BBC micro:bit (mpy sim, mpy test - deska "microbit").

Simulovaný micro:bit je sám - zprávy, které pošle, nikdo nepřijme
(konzole: Radio: odeslano "ahoj"). Zprávy od jiného micro:bitu podstrčí test:

    import radio
    radio.prijmi("ahoj")            # jako by ji poslal jiny micro:bit
    radio.on()
    radio.receive()                 # -> "ahoj"
    radio.odeslane()                # co program poslal: ["ahoj", b"\\x01\\x02"]

Pomocné funkce prijmi() a odeslane() na desce nejsou.
"""

try:
    from . import _rezim
    from . import utime as _utime
except ImportError:
    import _rezim
    import utime as _utime

RATE_1MBIT = 1
RATE_2MBIT = 2

_HLAVICKA = b"\x01\x00\x01"         # send() posila text s touto hlavickou (jako na desce)
_VYCHOZI = {"length": 32, "queue": 3, "channel": 7, "power": 6,
            "address": 0x75626974, "group": 0, "data_rate": RATE_1MBIT}

_stav = {"zapnuto": False}
_nastaveni = dict(_VYCHOZI)
_fronta = []                        # prijate zpravy: (data, rssi, cas_us)
_odeslane = []


def on():
    _stav["zapnuto"] = True


def off():
    _stav["zapnuto"] = False


def config(**kwargs):
    for klic, hodnota in kwargs.items():
        if klic not in _VYCHOZI:
            raise TypeError("unexpected keyword argument '%s'" % klic)
        _nastaveni[klic] = int(hodnota)


def reset():
    _nastaveni.clear()
    _nastaveni.update(_VYCHOZI)


def _zapnute():
    if not _stav["zapnuto"]:
        raise ValueError("radio is not enabled")


def send_bytes(message):
    _zapnute()
    data = bytes(message)[:_nastaveni["length"]]
    _odeslane.append(data)
    if data.startswith(_HLAVICKA):
        _rezim.oznam("radio", "odeslano", data[len(_HLAVICKA):].decode("utf-8", "replace"))
    else:
        _rezim.oznam("radio", "odeslano", data)


def send(message):
    send_bytes(_HLAVICKA + str(message).encode("utf-8"))


def receive_full():
    _zapnute()
    return _fronta.pop(0) if _fronta else None


def receive_bytes():
    zprava = receive_full()
    return zprava[0] if zprava else None


def receive():
    data = receive_bytes()
    if data is None:
        return None
    if not data.startswith(_HLAVICKA):
        raise ValueError("received packet is not a string")
    return data[len(_HLAVICKA):].decode("utf-8", "replace")


# ---------------------------------------------------------
# Pomocne funkce pro testy (na desce nejsou)
# ---------------------------------------------------------

def prijmi(zprava, rssi=-50):
    """Zprava od jineho micro:bitu: text (jako send) nebo bajty (jako send_bytes).
    Plna fronta (config queue=3) dalsi zpravu zahodi - jako na desce."""
    data = _HLAVICKA + zprava.encode("utf-8") if isinstance(zprava, str) else bytes(zprava)
    if len(_fronta) < _nastaveni["queue"]:
        _fronta.append((data[:_nastaveni["length"]], int(rssi), _utime.ticks_us()))


def odeslane():
    """Co program poslal: texty (send) jako str, ostatni jako bytes."""
    return [d[len(_HLAVICKA):].decode("utf-8", "replace") if d.startswith(_HLAVICKA) else d
            for d in _odeslane]


def _reset():
    _stav["zapnuto"] = False
    reset()
    _fronta.clear()
    _odeslane.clear()


_rezim.pri_resetu(_reset)
