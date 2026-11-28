# MicroPython na BBC micro:bitu

Tento návod vysvětluje, čím se **BBC micro:bit** liší od ostatních desek s MicroPythonem v kurzu (Raspberry Pi Pico, Pico:ed) a proč nástroj `mpy` dělá u micro:bitu některé věci jinak. Všechna čísla jsou naměřená na **micro:bitu v2** (MicroPython 1.15) dne 27. 11. 2026. micro:bit v1 jsme zatím neměřili.

Běžnou práci s MicroPythonem popisuje [MicroPython.md](MicroPython.md), vnitřní fungování nástrojů [Nastroje.md](Nastroje.md).

---

## 1. Shrnutí pro spěchající

- **Úložiště má jen asi 20 kB.** Dřív dojde místo pro soubory než paměť RAM. Program s knihovnou kolem 19 kB se vejde jen na úplně prázdnou desku.
- **Nemá složky.** Na desku jdou jen soubory z kořene projektu; knihovny ze složek (`lib/`, `lib_mpy/`) se na micro:bit nenahrávají. Vlastní moduly dávejte vedle `main.py`.
- **Je na něm starší MicroPython** (1.15). Nezná **f-řetězce** `f"..."`, texty skládejte pomocí `+`.
- **Zmenšení souborů pomáhá.** `mpy minify simple` odstraní komentáře a dokumentaci, soubory jsou o 30–45 % menší. `mpy minify full` přejmenuje i lokální proměnné, v našich knihovnách to ušetřilo dalších asi 15 %. `mpy minify max` sloučí program s jeho moduly do jednoho `main.py` a přejmenuje všechno. Je to poslední záchrana, protože chybové hlášky pak přestanou dávat smysl.
- **Přenos občas selže** falešnou chybou `SyntaxError`. `mpy` to pozná, vypíše důvod a příkaz sám zopakuje.
- **Bez desky** program vyzkouší `.\mpy sim --microbit` (s připojeným micro:bitem stačí `.\mpy sim`), viz [kapitola 8](#8-simulace-na-pc-mpy-sim---microbit).

---

## 2. Čím se micro:bit liší

| | Raspberry Pi Pico | BBC micro:bit v2 |
|---|---|---|
| MicroPython | 1.27 | 1.15 (vlastní varianta pro micro:bit) |
| Úložiště | asi 1,4 MB, se složkami | **asi 20 kB, bez složek** |
| Volná RAM po startu | asi 240 kB | asi 64 kB |
| f-řetězce `f"..."` | ano | **ne** (umí je až MicroPython 1.17) |
| Předpřeložené soubory `.mpy` | ano | **ne** (soubor `.mpy` deska vůbec nehledá) |
| Moduly `json`, `re`, `hashlib`, `io` | ano | **ne** |
| `os.mkdir`, `os.rmdir` | ano | **ne** |
| `os.listdir('/')` | ano | ne, jen `os.listdir()` bez cesty |
| Hardware | modul `machine` | modul `microbit` (`pin0`, `display`, `button_a`, …) |
| USB (VID:PID) | `2E8A:0005` | `0D28:0204` (rozhraní DAPLink) |

Podle VID:PID `0D28:0204` nástroj `mpy` pozná, že jde o micro:bit, a přepne se na ploché úložiště (tabulka `MP_FLAT_USB` v `deska.py`).

---

## 3. Úložiště: proč dojde místo

### Kolik místa je

Na prázdné desce s `main.py` o velikosti 3 kB je volných **16 960 B**, celkem má úložiště asi **20 kB**. Když dojde místo, nahrávání skončí chybou `No space left on device`. Rozepsaný soubor micro:bit sám zahodí.

### Místo se přiděluje po blocích 128 B

Každý soubor zabere celé bloky po 128 B. Asi 126 B z bloku jsou data, první blok nese i jméno souboru. I soubor o 1 B tedy zabere 128 B.

Naměřená cena za počet souborů, kdy se stejný kód (2 706 B) rozdělil do více modulů:

| Modulů | Zabráno v úložišti | Ztráta | RAM po importu | RAM navíc |
|---|---|---|---|---|
| 1 | 2 752 B | +46 B | 5 424 B | – |
| 2 | 2 752 B | +46 B | 5 360 B | (šum) |
| 4 | 3 008 B | +302 B | 5 600 B | +176 B |
| 8 | 3 008 B | +302 B | 5 984 B | +560 B |
| 16 | 4 032 B | +1 326 B | 6 512 B | +1 088 B |

**Každý soubor navíc stojí asi 85 B úložiště a 70 B RAM.** U projektu s pěti moduly je to dohromady jen asi 350 B. Rozdělit kód do více souborů je tedy v pořádku, místo ušetří spíš zmenšení (kapitola 5).

### Smazané místo se neuvolní hned

Po smazání souboru micro:bit místo hned nevrátí, uvolní ho až při dalším zápisu do plna. Proto se stejný program může jednou vejít a jindy ne. Na čerstvě smazanou desku (`mpy wipe`) se vejde nejvíc.

### Jak zjistit, kolik místa zbývá

`mpy list` a `mpy check` u micro:bitu vypíšou odhad podle bloků po 128 B:

```text
Uloziste micro:bitu: obsazeno asi 15.0 kB z asi 19.7 kB (volno asi 4.7 kB, 76 %)
```

---

## 4. Paměť RAM

RAM (asi 64 kB volných) na micro:bitu v2 obvykle nedojde. Import knihovny `cely_projekt` (14,6 kB zdrojáku) zabral 9,4 kB RAM. Zmenšení souborů RAM skoro nešetří: deska stejně ukládá přeložený kód, ne zdroják.

| `cely_projekt.py` | Soubor | RAM po importu |
|---|---|---|
| původní | 14 662 B | 9 360 B |
| zmenšený `simple` | 10 323 B | 9 136 B |
| zmenšený `full` | 8 261 B | 10 944 B |

U `full` je RAM dokonce víc: opakované konstanty se uloží do proměnných modulu, a ty v paměti zůstávají.

micro:bit v1 má jen 16 kB RAM. Tam může dojít paměť už při překladu velkého souboru (`MemoryError`), zatím jsme to ale neměřili.

---

## 5. Zmenšení souborů (`mpy minify`)

### Proč

Úložiště je úzké hrdlo. Knihovna `cely_projekt` (projekt `robotprogramming`, 14,6 kB) a program, který ji používá (4,6 kB), dohromady 19,2 kB, se vejdou jen na čerstvě smazanou desku. Autoři kvůli velikosti museli z knihovny vyřadit světla. Zmenšení ušetří tisíce bajtů:

| Program + knihovna | Velikost | Vejde se? |
|---|---|---|
| původní | 19 246 B | jen na prázdnou desku |
| knihovna zmenšená `simple` | 14 907 B | ano, volno asi 4,7 kB |
| knihovna zmenšená `full` | 12 845 B | ano, volno asi 6,8 kB |
| obojí sloučené `max` | 9 437 B | ano, volno asi 10,3 kB |

### Jak

Jeden přepínač, který si projekt pamatuje zvlášť pro MicroPython (`mpy`) a CircuitPython (`cpy`):

```powershell
.\mpy minify            # stav a kolik by se v projektu ušetřilo
.\mpy minify simple     # jednoduché zmenšení
.\mpy minify full       # plné zmenšení
.\mpy minify max        # sloučení do jednoho main.py (jen mpy)
.\mpy minify off        # vypnout
```

| Úroveň | Co udělá | Úspora (`cely_projekt`) |
|---|---|---|
| `off` | nic | – |
| `simple` | odstraní komentáře, dokumentační řetězce a zbytečné mezery; **jména zůstanou** | 29 % |
| `full` | navíc přejmenuje **lokální proměnné** ve funkcích na krátká jména a opakované konstanty dá do proměnné | 43 % |
| `max` | `main.py` a místní moduly, které importuje, **sloučí do jednoho `main.py`** a přejmenuje i třídy, funkce a globální proměnné (jen `mpy`) | 50 % (program + knihovna) |

Pravidla:
- Zmenšuje se **jen to, co jde na desku**. Soubory v projektu zůstanou, jak jsou.
- **`main.py`, `code.py` a `boot.py` se nezmenšují** (kromě úrovně `max`). Ty si ladíte vy a čísla řádků v chybové hlášce musí sedět s editorem.
- U ostatních souborů (knihoven) chybová hláška ukáže **jiné číslo řádku**, než vidíte v editoru. Když hledáte chybu v konkrétní knihovně, vyřaďte ji ze zmenšení: `.\mpy minify exclude lib/robot.py` (zpět: `minify include`). Ostatní soubory zůstanou zmenšené. Masky fungují jako v `.vscode/upload.toml`: `robot.py` (jméno kdekoliv), `/robot.py` (jen v kořeni), `lib_mpy/` (celá složka).
- `full` nepřejmenuje třídy, funkce ani globální proměnné, protože je importují jiné soubory (`from cely_projekt import Robot`).
- Jména, která se nesmí přejmenovat nikdy, přidáte příkazem `.\mpy minify keep jmeno1 jmeno2` (odebrání: `minify unkeep`).
- Nastavení je v souboru `.vscode/deska.json`, který patří do gitu. Učitel ho tak může v šabloně přednastavit.
- Nezměněné soubory se při dalším nahrání pořád přeskočí: porovnává se už zmenšený obsah.
- Zmenšuje knihovna `python-minifier`, kterou nainstaluje setup.

Totéž (kromě `max`) umí `cpy minify`, ale u CircuitPythonu (disk 1 MB) to obvykle potřeba není.

**Co uvidíte při nahrání.** Když je zmenšení vypnuté, `mpy upload` napíše jen `zmenseni: vypnute`. Když je zapnuté, vypíše úroveň a co se zmenší a co ne:

```text
   zmenseni:    ZAPNUTE - simple (jednoduche)
   zmensi se:   lib/pozdrav.py
   nezmensi se: main.py (vychozi - ladis ho), lib/texty.py (minify exclude)
   ...
   zmenseno:    1 souboru 449 B -> 251 B (usetreno 198 B)
```

### Úroveň `max`: sloučení do jednoho souboru

`main.py` a všechny **místní** moduly, které importuje (i nepřímo; na micro:bitu jen z kořene projektu, na Picu i z knihoven, které jdou do `/lib`), se sloučí do jednoho `main.py` v pořadí podle závislostí. Výsledek se zmenší včetně přejmenování tříd, funkcí a globálních proměnných. Na desku jde jen sloučený `main.py`.

- **Cena:** chybová hláška pak mluví o třídách `A`, `D` a řádcích, které v editoru nenajdete, a to i v `main.py`. Používejte `max` jen tehdy, když se program nevejde ani s `full`.
- Bloky `if __name__ == "__main__":` v importovaných modulech (jejich vlastní testy) se vynechají, jinak by se po sloučení spustily.
- Modul vyřazený přes `minify exclude` se nesloučí: zůstane jako samostatný soubor se svými jmény a program ho normálně importuje.
- Balíčky ve složkách (např. `lib_mpy/picoed_v2_lib/` na Picu) se neslučují a zůstanou jako cizí knihovny.
- **Moduly, které `main.py` nepoužívá** (ani přímo, ani přes jiný modul), se při `max` na desku **vůbec nenahrají** – MicroPython spouští jen `main.py` a místo je drahé. Výpis to řekne řádkem `nenahraje se:`, přehled ukáže `.\mpy files`. Datové soubory (`.txt`, `.csv`) se nahrají vždy. Pozor: jiný program spuštěný přes `.\mpy runmain soubor.py` své moduly hledá na desce – pak použijte `mpy minify full` (`runmain` na to upozorní).
- Sloučení **odmítne** (s vysvětlením a radou použít `full`) program, ve kterém je `import modul` (použití `modul.neco`), `from modul import *`, import místního modulu uvnitř funkce nebo podmínky, relativní import, kruhový import, nebo stejné jméno definované ve dvou modulech. Co by `max` udělal, ukáže předem `mpy minify`.
- Vyzkoušeno: zkušební program se dvěma moduly se po sloučení spustil správně na micro:bitu i na Picu. Sloučený `cely_projekt` + program (9 437 B) se na micro:bitu přeloží a naimportuje (RAM 9 104 B).

### Co jsme nezvolili

- **Sloučení jako výchozí volba.** Samo ušetří jen zmíněných asi 85 B za soubor; velkou úsporu dá až přejmenování tříd a globálních jmen, a to kazí chybové hlášky. Proto je jen jako `max`, ne jako běžná úroveň.
- **Předpřeložené soubory `.mpy`** (nástroj `mpy-cross`). micro:bit v2 je nenačte: soubor `.mpy` verze 5, správné pro MicroPython 1.15, skončí chybou `ImportError: no module named`.

---

## 6. Chyby přenosu a jejich příčiny

Na micro:bitu `mpremote` občas skončí chybou `SyntaxError: invalid syntax` v kódu, který **sám** posílá na desku. Kód dorazí poškozený, nejspíš kvůli řízení toku při přenosu. Stejný příkaz napodruhé projde. Naměřeno: 3 ze 101 příkazů. Stejný problém nejspíš řeší i nástroj `misync` (projekt `microbit-sync`), který nahrávání opakuje, dokud neprojde.

`mpy` proto z výstupu `mpremote` pozná, **proč** příkaz selhal, a vypíše to před opakováním:

| Výstup `mpremote` | Příčina | Opakuje se? |
|---|---|---|
| `SyntaxError` (v kódu mpremote) | chyba přenosu | ano, až dvakrát |
| `TransportError`, `timeout`, `SerialException` | spojení se přerušilo | ano |
| `could not enter raw repl` | běžící program blokuje desku | ano |
| `No space left on device` | v úložišti došlo místo | ne, poradí `mpy list`, `mpy minify`, `mpy wipe` |
| `MemoryError` | došla paměť RAM | ne |
| `failed to access`, `Access is denied`, `in use` | port drží jiný program | ne |

Ukázka:

```text
POZOR: chyba prenosu: kod, ktery mpremote poslal na desku, dorazil poskozeny (SyntaxError) - opakuji (1/2)
```

Program studenta (`mpy runmain`) se neopakuje, protože tam může být `SyntaxError` opravdová chyba v programu.

---

## 7. Co si pohlídat při psaní programu pro micro:bit

- **Žádné f-řetězce.** Místo `print(f"Vzdalenost: {cm}")` pište `print("Vzdalenost: " + str(cm))`. S f-řetězcem program skončí hned po spuštění chybou `SyntaxError`.
- **Moduly jako soubory v kořeni projektu** (např. `robot.py` vedle `main.py`). Složky s knihovnami se na micro:bit nenahrávají; co přesně se nahraje, ukáže `.\mpy files microbit`.
- **Hlídejte velikost.** Velké komentáře a dokumentační řetězce v knihovnách zabírají místo, které `mpy minify simple` vrátí. Vlastní program (`main.py`) se nezmenšuje, ať v něm chyby snadno najdete.
- **Před nahráním většího projektu** použijte `mpy wipe`. Na čerstvě smazanou desku se vejde nejvíc.

---

## 8. Simulace na PC (`mpy sim --microbit`)

Program pro micro:bit jde vyzkoušet i bez desky. `.\mpy sim` simuluje micro:bit sám, když je micro:bit připojený; jinak ho vybere volba `.\mpy sim --microbit` (jiný soubor: `.\mpy sim muj.py --microbit`). Program běží beze změny – místo vestavěných modulů micro:bitu se použijí falešné ze složky `pc/_fake`:

| Modul | Co umí |
|---|---|
| `microbit` (`pc/_fake/microbit.py`) | displej 5 × 5 s jasem 0–9 (`show`, `scroll`, `set_pixel`, `get_pixel`, `clear`), `Image` včetně vestavěných obrázků (`Image.HEART`, …), tlačítka `button_a` / `button_b`, piny `pin0`–`pin20` (`read_digital`, `write_digital`, `read_analog`, `write_analog`, `is_touched`), dotykové logo, `i2c`, `uart`, `spi`, akcelerometr, kompas, mikrofon, `sleep`, `running_time`, `temperature` |
| `music` | `play` (i vestavěné melodie `music.NYAN`, …), `pitch`, `stop`, `set_tempo` |
| `neopixel` | `NeoPixel(pin, počet)`, barvy se vypíšou při `show()` |
| `radio` | `send` / `receive`; simulovaný micro:bit je sám, zprávy od jiného podstrčí jen test |
| `machine` | jen to, co má micro:bit: `time_pulse_us` (ultrazvuk), `reset`, … |

```text
Spusteno main.py na desce: BBC micro:bit
[     0.05 s] Displej: text "ZSaPR"
[     4.55 s] Displej:
               .....
               .....
               ..#..
               .....
               .....
```

Klávesy: `a` / `b` = tlačítko A / B, `l` = dotyk loga, `q` nebo `Ctrl+C` = konec.

Našeptávání v editoru (Pylance) zná moduly `microbit`, `music` a `radio` z typových definic `pc/_stubs/*.pyi` – u `display.`, `pin0.` nebo `music.play(` ukáže metody a jejich popis česky.

Simulace se chová jako deska i v tom, co micro:bit **nemá**: knihovny ze složek `lib/` a `lib_mpy/` nejsou k dispozici a `from machine import Pin` skončí chybou. Čekání (`sleep`) i rolování textu trvají přibližně jako na desce a `sleep(0.5)` nečeká vůbec – bere milisekundy, stejně jako na desce.

Na co simulace nepřijde:

- **f-řetězce**: program běží v Pythonu na PC, kde `f"..."` funguje. Na micro:bitu skončí chybou `SyntaxError` (viz kapitola 7).
- **Málo místa a paměti**: na PC se vejde všechno.
- **Tvary písmen**: `display.show("A")` a `display.scroll("Ahoj")` se vypíšou jako text, body displeje se nerozsvítí (`get_pixel` vrátí 0).
- **Robot**: na I2C nic není. Program, který čte senzory nebo řídí motory robota (např. `i2c.read(0x38, 1)`), skončí chybou `OSError: [Errno 19] ENODEV` – stejně jako micro:bit bez robota.

**Testy** (`.\mpy test`) běží na Pico:ed. Test pro micro:bit si desku vybere v `setUp`:

```python
from _fake._desky import nastav as nastav_desku

class TestMujProgram(unittest.TestCase):
    def setUp(self):
        nastav_desku("microbit")
        import microbit             # az po nastav_desku
        self.microbit = microbit
```

Falešný `microbit` má pro testy pomocné funkce (na desce nejsou): `stiskni("a")`, `displej().svitici()` (co ukazuje displej), `displej().text`, `nastav_vstup(pin0, 1)`, `nastav_analog(pin1, 512)`, `nastav_pulz(pin2, 580)`, `dotkni(pin0)`, `historie(pin8)`, `pridej_i2c(0x38)` (zařízení na I2C), `nastav_naklon(x, y, z)`, `nastav_gesto("shake")`, `nastav_teplotu(25)` a další; `radio.prijmi("zprava")` a `radio.odeslane()`. Ukázka je v `pc/tests_mpy/test_main_py_microbit.py`.

---

## 9. Jak se měřilo

- **Úložiště:** na desce se zapisoval zkušební soubor po 64 B, dokud nedošlo místo, pak se smazal. Měření se opakovalo, dokud dvě po sobě nedala stejnou hodnotu (kvůli pozdnímu uvolnění smazaného místa).
- **RAM:** `gc.mem_free()` před importem a po něm, po měkkém restartu desky. Importovaly se jen moduly, které definují třídy; programy (za `if __name__ == "__main__":`) se nespouštěly.
- **Kód:** knihovny z projektu `robotprogramming` (`cely_projekt`, složka `stary/`) bez robota JoyCar.
