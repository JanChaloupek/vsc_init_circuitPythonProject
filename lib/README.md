# lib/ – společné knihovny

Knihovny v čistém Pythonu, které fungují na **CircuitPythonu i MicroPythonu** (kromě micro:bitu).

| Složka v projektu | Na kterou desku jde | Kam na desce |
|---|---|---|
| `lib/` | CircuitPython, MicroPython na Picu / Pico:edu | `/lib` |
| `lib_cpy/` | jen CircuitPython | `/lib` |
| `lib_mpy/` | jen MicroPython na Picu / Pico:edu | `/lib` |

- Na desce jsou všechny tři složky v **jedné** složce `/lib`. Dva soubory se stejným jménem (např. `lib/robot.py` a `lib_mpy/robot.py`) nahrávání odmítne.
- **BBC micro:bit** nemá složky, knihovny ze složek se na něj nenahrávají. Moduly pro micro:bit patří do kořene projektu (vedle `main.py`).
- Import je stejný jako na desce: `from robot import Robot` (ne `from lib.robot import ...`).
- Co a kam se nahraje, ukáže `.\cpy files` nebo `.\mpy files`. Pravidla jsou v `.vscode/upload.toml`.
