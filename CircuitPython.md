# Práce s CircuitPythonem ve Visual Studio Code (GUI & CLI)

Tato příručka detailně popisuje kompletní vývojový cyklus v **CircuitPythonu** v připraveném prostředí editoru Visual Studio Code. Zahrnuje popis cílových desek **Pico:ed verze 1 a verze 2**, práci se souborem **`code.py`**, **grafické rozhraní (GUI)** s automatickým nahráváním při uložení i **příkazovou řádku (CLI)**.

---

## 1. Které desky v projektu používají CircuitPython

> [!IMPORTANT]
> **V tomto projektu je CircuitPython vyhrazen VÝHRADNĚ pro desky:**
> 1. **ELECFREAKS Pico:ed verze 1** (s čipem Raspberry Pi RP2040 ve tvaru micro:bit sběrnice)
> 2. **ELECFREAKS Pico:ed verze 2** (s čipem Raspberry Pi RP2040 ve tvaru micro:bit sběrnice)
>
> Desky **BBC micro:bit** a samostatné **Raspberry Pi Pico** v tomto kurzu běží na **MicroPythonu** (CircuitPython na nich nepoužíváme, viz `MicroPython.md`).

### Rozdíly mezi Pico:ed v1 a Pico:ed v2 v CircuitPythonu:
- **Pico:ed v1:** Bzučák je připojen na pin `GP0`.
- **Pico:ed v2:** Bzučák je připojen na pin `GP3`, vylepšeno napájení a rozložení pinů.
- **Společné vlastnosti:** Obě desky mají procesor Raspberry Pi RP2040, maticový LED displej 17×7 (ovládaný čipem IS31FL3731), tlačítka A a B a stavovou modrou LED diodu na pinu GP25.
- **Vestavěný modul `picoed`:** Firmware CircuitPythonu pro Pico:ed obsahuje přímo v sobě zabudovaný modul `picoed`, takže není nutné nahrávat žádné externí knihovny pro základní funkce.

---

## 2. Hlavní program: `code.py`

Soubor **`code.py`** v kořeni projektu je **hlavním spouštěným skriptem pro CircuitPython**.

### Jak se `code.py` spouští:
1. Po připojení desky do USB portu se v počítači objeví flash disk s názvem **`CIRCUITPY`**.
2. Mikrokontrolér automaticky načte a spustí soubor `code.py`.
3. Kdykoliv soubor upravíte a v editoru uložíte (`Ctrl+S`), CircuitPython automaticky detekuje zápis na disk a **okamžitě provede soft reload kódu**.

### Co dělá výchozí starter `code.py`:
- Importuje vestavěný modul `picoed` (`from picoed import led, display`).
- Zaroluje na 17×7 matici uvítací nápis `"ZSaPR"`.
- V hlavní smyčce `while True:` v intervalu 1 s přepíná stavovou LED diodu (`led.toggle()`).
- Pokud je kód spuštěn offline na PC bez připojené desky, bezpečně využije simulační vrstvu `_fake/` a vypisuje stav do konzole.

### Možnosti rozšíření v `code.py` pro desky Pico:ed:
```python
import time
from picoed import display, led, button_a, button_b

# 1. Zobrazeni textu na maticovem displeji 17x7
display.scroll("Ahoj robote!")

# 2. Interakce s tlacitky A a B
while True:
    if button_a.is_pressed():
        led.on()
        display.show("A")
    elif button_b.is_pressed():
        led.off()
        display.show("B")
    time.sleep(0.05)
```

---

## 3. Jednorázová příprava prostředí (Setup)

Před první prací spusťte jednorázový instalační skript:

- **Na Windows:** dvojklikem spusťte **`setup.bat`** v kořeni projektu.
- **Na Linuxu a macOS:** v terminálu spusťte **`./setup.sh`**. Tady je **povinný**: nastavení je připravené pro Windows (příkaz `python`) a skript ho přepíše na `python3`. Bez něj nefunguje nahrávání po `Ctrl+S` ani tlačítka panelu.

Skript nainstaluje Python knihovny (`mpremote`, který obsahuje i `pyserial`, a `matplotlib` pro graf), rozšíření VS Code a nastaví tlačítka panelu i automatické nahrávání po `Ctrl+S`. Na konci vypíše, jaké desky jsou připojené.

### Důležitá nainstalovaná rozšíření pro CircuitPython:
- **`emeraldwalk.runonsave`** (Run on Save) – po stisku `Ctrl+S` zkopíruje uložený soubor na disk robota.
- **`JanChaloupek.micropython-panel`** – panel a tlačítka ve stavovém řádku pro MicroPython i CircuitPython.
- **`wmerkens.vscode-circuitpython-v2-cursor-ai`** – nápověda pinů a dokumentace pro desky s CircuitPythonem.
- **`ms-python.vscode-pylance`** – našeptávání kódu a typová kontrola.

---

## 4. Práce v grafickém rozhraní VS Code (GUI)

Vývoj v CircuitPythonu je navržen tak, aby student nemusel nic nahrávat ručně myší.

### A) Automatické nahrávání při uložení (Run on Save)
1. Otevřete soubor **`code.py`** a upravte algoritmus.
2. Stiskněte **`Ctrl+S`** (na macOS **`Cmd+S`**).
3. Rozšíření *Run on Save* na pozadí spustí příkaz `cpy save` (`python .vscode/deska.py cpy save <soubor>`).
4. Ten najde připojený disk robota:
   - **Windows:** disková jednotka s názvem svazku `CIRCUITPY` (např. `D:`, `F:`).
   - **macOS:** svazek `/Volumes/CIRCUITPY`.
   - **Linux:** `/media/$USER/CIRCUITPY`, `/run/media/...` nebo `/mnt/CIRCUITPY`.
5. Soubor se zkopíruje na desku (jen když se liší od toho, co na desce už je) a **CircuitPython sám spustí nový kód** – tomu se říká *autoreload*.

Run on Save sleduje soubory `.py`, `.toml`, `.json`, `.txt` a `.csv`. Jestli se soubor opravdu zkopíruje, rozhodne `.vscode/.ignoreCopy` (viz B).

**Kde zjistit, co se stalo:** panel *Output* (`Ctrl+Shift+U`) → v rozbalovacím seznamu vpravo vyberte *Run On Save*. Výpis jde po očíslovaných krocích, takže je vidět, kde se kopírování zastavilo:

```text
Run on Save: kopirovani ulozeneho souboru na desku CIRCUITPY (09:22:58)
1) Ulozeny soubor          - jaký soubor, jeho velikost a čas uložení
2) Pravidla                - jestli ho .ignoreCopy nevylučuje (a kterou maskou)
3) Disk desky CIRCUITPY    - kde je disk, volné místo, verze firmwaru
4) Cil na desce            - co tam teď je a jestli se obsah liší
5) Kopirovani              - výsledek zápisu
Hotovo: code.py -> F:\code.py. CircuitPython program sam restartuje (autoreload).
```

Když se něco nepovede, výpis skončí řádkem `ERROR: v kroku N - …` s radou, co dělat (např. `v kroku 3 - disk CIRCUITPY nenalezen`). Stejný výpis dostanete i ručně v terminálu: `.\cpy save code.py`.

> [!TIP]
> Když uložíte několik souborů rychle za sebou, CircuitPython počká, až zápisy ustanou (asi 0,5 s), a program restartuje **jen jednou**.

### B) Co se na desku kopíruje (`.vscode/.ignoreCopy`)
Na desku patří jen to, co program potřebuje ke svému běhu. Soubor **`.vscode/.ignoreCopy`** obsahuje masky toho, co se **nekopíruje** – každý řádek jedna maska. Hlavní položky:

| Maska | Proč se nekopíruje |
|---|---|
| `main.py` | program pro MicroPython – CircuitPython by ho spustil, kdyby chyběl `code.py` |
| `_stubs/*`, `_fake/*` | nápověda pro editor a simulace hardwaru pro PC |
| `lib/picoed_v2_lib/*` | knihovna pro MicroPython (CircuitPython má modul `picoed` vestavěný) |
| `tests/*`, `run_test.py` | testy, které běží na PC |
| `*.md`, `*.bat`, `*.cmd`, `*.sh`, `*.ps1` | dokumentace a spouštěcí skripty |

- `*` znamená „cokoliv“ (i přes více složek), `**` znamená totéž.
- Skryté položky (`.git`, `.vscode`, ...) a `__pycache__` se nekopírují nikdy.
- Stejná pravidla platí pro `Ctrl+S` i pro příkaz `cpy upload`.
- Řádky začínající `#` jsou komentáře – soubor sám vysvětluje, proč tam která maska je.
- Chcete-li na desku nenahrávat další soubor (např. `poznamky.txt`), přidejte jeho jméno na nový řádek.

### C) Tlačítka v panelu a ve stavovém řádku
Tlačítka přidává rozšíření **MicroPython & CircuitPython Panel**. Postranní panel otevřete ikonou čipu v levém svislém pruhu. Je to **rychlý přístup k základním akcím**: blok **CircuitPython** ukazuje připojenou desku (např. `COM5 · F:\`, jméno desky a verzi firmwaru) a čtyři tlačítka. Když žádná deska s CircuitPythonem připojená není, je blok ztlumený.

| Tlačítko | Co udělá | Sériový port |
|---|---|---|
| **⬆ Nahrát projekt** | nahraje projekt na disk `CIRCUITPY` (`cpy upload`) | ne |
| **↻ Restartovat program** | znovu spustí `code.py` (`cpy reset`) | ano |
| **⌨ Konzole (REPL)** | zastaví program a otevře konzoli Pythonu na desce (`cpy repl`) | ano |
| **🗑 Smazat desku** | smaže obsah disku `CIRCUITPY` – VS Code se nejdřív zeptá v dialogu (`cpy wipe`) | ne |

Ve spodním stavovém řádku jsou s ikonami `CPY Upload` a `CPY REPL` (a jejich `MPY` protějšky). Blok **MicroPython** je pro desky s MicroPythonem (viz `MicroPython.md`). Tlačítko otevře terminál *MicroPython* a příkaz v něm spustí.

Další příkazy (výpis souborů, sledování výstupu, graf, diagnostika, …) jsou v terminálu – viz kapitola 5 a `.\cpy help`. Panel na ně odkazuje dole.

### D) Sledování výstupů (Serial Monitor)
Pro čtení výpisů z funkce `print(...)`:
1. V editoru VS Code klikněte v dolním stavovém řádku na sériový port (nebo stiskněte `Ctrl+Shift+P` → `Serial Monitor: Focus on Serial Monitor View`).
2. Vyberte COM port desky Pico:ed a zvolte rychlost **`115200`** baudů.
3. V okně *Serial Monitor* vidíte veškeré výpisy senzorů i chybová hlášení v reálném čase.

> [!NOTE]
> **Práce se soubory sériový port nepoužívá.** `Ctrl+S`, `cpy upload`, `cpy main`, `cpy list`, `cpy wipe` a `cpy setup` zapisují a čtou přímo disk `CIRCUITPY`, takže fungují i s otevřeným Serial Monitorem – výstup nového programu v něm rovnou uvidíte.
>
> Sériový port potřebují jen příkazy, které s deskou „mluví“: `cpy repl`, `cpy runmain`, `cpy monitor`, `cpy plot`, `cpy stop`, `cpy reset`, `cpy check`, `cpy wipe --format` a `cpy bootloader`. Port může mít otevřený vždy jen jeden program, proto před nimi Serial Monitor odpojte (ikona *Stop Monitoring*). Když to neuděláte, `cpy` napíše `Port COMx nelze otevřít`.

---

## 5. Práce v příkazové řádce (CLI)

Terminál otevřete klávesou `Ctrl+~`. Všechny příkazy jsou v nástroji **`cpy`**. Má stejné příkazy jako `mpy` pro MicroPython, takže se nemusíte učit dvě sady.

- **Windows – PowerShell** (výchozí terminál ve VS Code): `.\cpy <příkaz>`
  (PowerShell nespouští programy z aktuální složky bez `.\` na začátku)
- **Windows – příkazový řádek cmd:** `cpy <příkaz>`
- **Linux a macOS:** `./cpy.sh <příkaz>`
- **Kdekoliv:** `python .vscode/deska.py cpy <příkaz>` (takhle příkazy volá panel)

**Podrobný výpis:** příkazy, které spouštějí tlačítka panelu a Run on Save (`save`, `upload`, `main`, `reset`, `repl`, `wipe`), vypisují očíslované kroky – co se nahrává, kde je disk a port, co se na desce liší, co se zapsalo, první výstup programu po restartu. Při chybě poslední řádek řekne, ve kterém kroku a co s tím (např. `ERROR: v kroku 2 - port COM5 nelze otevrit` + rada odpojit Serial Monitor).

### A) Základní příkazy

```bash
# Zobrazení nápovědy
cpy help

# 1. Nahrání projektu (jen změněné soubory; --all = všechny)
#    Soubory se zapisují přímo na disk jako při Ctrl+S, nový kód spustí autoreload.
#    Co se nahrává, určuje .vscode/.ignoreCopy. Sériový port se nepoužívá.
#    --watch = po nahrání poslouchá sériový port a ukáže první výstup programu (nebo chybu).
cpy upload

# 2. Nahrání POUZE souboru code.py
cpy main

# 3. Spuštění code.py (nebo jiného souboru) z RAM bez zápisu na disk
#    Pozor: moduly, které program importuje (např. robot.py), se berou z desky.
#    cpy upozorní, když jsou na desce starší verze.
cpy runmain
cpy runmain test_motoru.py

# 4. Interaktivní REPL konzole (ukončení Ctrl+], Ctrl+D = restart code.py)
cpy repl

# 5. Stromový výpis souborů na desce včetně velikostí a volného místa
cpy list

# 6. Smazání všech souborů z desky (s potvrzením; --format = přeformátování disku)
cpy wipe

# 7. Diagnostika: disk, verze firmwaru, port, test REPL, nouzový režim
cpy check

# 8. Kompletní příprava desky (Wipe -> Upload -> List)
cpy setup

# 9. Restart programu (--hard = restart celé desky)
cpy reset

# 10. Živý graf hodnot, které program vypisuje (viz C)
cpy plot

# 11. Jaké desky jsou připojené (CircuitPython i MicroPython)
cpy devices
```

### B) Příkazy jen pro CircuitPython

| Příkaz | Co dělá |
|---|---|
| `cpy save <soubor>` | zkopíruje jeden soubor – to volá Run on Save po `Ctrl+S` |
| `cpy stop` | zastaví program (`Ctrl+C`), deska zůstane v REPL; `--wait` nejdřív počká na připojení desky |
| `cpy monitor` | sleduje výstupy `print()` bez zásahu do desky; `--restart` program nejdřív spustí znovu |
| `cpy lib install <jméno>` | knihovny z Adafruit Bundle přes nástroj `circup` (viz kapitola 6) |
| `cpy open` | otevře disk `CIRCUITPY` ve správci souborů |
| `cpy bootloader` | přepne desku do režimu BOOTSEL (disk `RPI-RP2`) |
| `cpy flash <soubor.uf2>` | nahraje firmware do desky |

Volby:
- `--port COMx` a `--drive F:` – když je připojeno víc desek (jinak se najdou samy),
- `-y` / `--yes` – bez potvrzovací otázky (pro `wipe`, `setup`, `flash`),
- `--watch` – u `upload`, `main`, `wipe`, `setup`: po zápisu poslouchá sériový port (nic do něj neposílá) a ukáže, jestli se program spustil a co vypsal. Vyžaduje odpojený Serial Monitor.
- `--stop` – u `upload`, `main`, `wipe`, `setup`: program se před zápisem přes sériový port zastaví a pak jednou spustí. Hodí se, když nahráváte hodně souborů nebo velké knihovny, nebo když program vypnul autoreload.

Bez `--watch` a `--stop` tyto příkazy sériový port vůbec nepoužívají.

`cpy stop --wait` pomůže, když program hned po startu desku „zahltí“ (např. nekonečná smyčka bez `time.sleep()`): spusťte příkaz, pak připojte desku a program se zastaví dřív, než stihne škodit.

### C) Živý graf hodnot (`cpy plot`)
Pro vizualizaci dat ze senzorů robota (např. ultrazvukový dálkoměr nebo senzory čáry) stačí v programu vypisovat čísla oddělená čárkou:

```python
import time
start = time.monotonic()
while True:
    cas = time.monotonic() - start
    print(cas, vzdalenost, rychlost)     # 1. číslo = osa X, další čísla = křivky
    time.sleep(0.05)
```

Pak v terminálu spusťte `cpy plot`. Otevře se okno s grafem, které se průběžně překresluje (posledních 500 měření). Řádky, které nejsou čísla (běžné výpisy), graf přeskočí. Když je na řádku jen jedno číslo, osa X je pořadové číslo měření. Graf ukončíte zavřením okna.

### D) Terminálový přístup k sériové lince
```bash
# Přes Python modul na libovolném OS:
python -m serial.tools.miniterm COMx 115200

# Na Linuxu a macOS:
screen /dev/ttyACM0 115200
```

Jak nástroj funguje uvnitř, popisuje **[Nastroje.md](Nastroje.md)**.

---

## 6. Knihovny pro CircuitPython (`CIRCUITPY/lib`)

Desky Pico:ed mají základní funkce v modulu `picoed`. Pokud potřebujete připojit další hardware (např. I2C expandéry PCA9555 / PCA9685, senzory prostředí):
- **Automaticky:** nainstalujte nástroj `circup` (`python -m pip install circup`) a pak:
  ```bash
  cpy lib install adafruit_pca9685     # nainstaluje knihovnu i její závislosti
  cpy lib list                         # které knihovny mají novější verzi
  cpy lib update                       # aktualizuje je
  ```
- **Ručně:** stáhněte oficiální Adafruit CircuitPython Bundle z [circuitpython.org/libraries](https://circuitpython.org/libraries) a zkopírujte příslušné soubory `.mpy` nebo `.py` do složky **`lib/`** na disku `CIRCUITPY`.

---

## 7. Offline vývoj a simulace (`_fake` a `_stubs`)

- Složka **`_fake/`** obsahuje simulaci modulů `picoed`, `board`, `digitalio`, `pwmio`, `neopixel` apod. Kód robota lze spustit přímo na PC bez připojené desky:
  ```bash
  python code.py
  ```
- Složka **`_stubs/`** v kombinaci s `pyrightconfig.json` zajišťuje plnohodnotné doplňování kódu (IntelliSense) bez falešných chyb v editoru.

---

## 8. Řešení častých potíží (Troubleshooting)

| Problém | Příčina | Řešení |
|---|---|---|
| **Disk CIRCUITPY se po zapojení neobjeví** | 1. Použit pouze nabíjecí kabel bez datových linek.<br>2. Na desce je nahrán MicroPython místo CircuitPythonu. | 1. Použijte kvalitní datový kabel.<br>2. Přepněte desku Pico:ed do režimu BOOTSEL a nahrajte firmware CircuitPythonu (`.uf2` pro Pico:ed). |
| **Deska bliká červeně / žlutě (Safe Mode)** | Kritická chyba hardware nebo odpojení USB kabelu během zápisu. | Otevřete soubor `boot_out.txt` na disku `CIRCUITPY`, kde je zapsán důvod pádu. Opravte chybu v `code.py` a stiskněte tlačítko RESET. |
| **Kód se neustále restartuje ve smyčce** | Ve VS Code je zapnuté automatické ukládání s příliš krátkým intervalem. | Vypněte v nastavení VS Code volbu `files.autoSave` a ukládejte kód manuálně klávesami `Ctrl+S`. |
| **`NameError: name '\ufeff' is not defined` na 1. řádku** | Soubor je uložený jako „UTF-8 with BOM“ (neviditelná značka na začátku, přidává ji např. Poznámkový blok). | `cpy` značku při kopírování odstraní sám a upozorní na to. Natrvalo: ve VS Code klikněte vpravo dole na `UTF-8 with BOM` → `Save with Encoding` → `UTF-8`. |
| **Linux/macOS: po `Ctrl+S` chyba `python: command not found`** | Nespustili jste `./setup.sh`. Nastavení je pro Windows (`python`), na Linuxu a macOS je potřeba `python3`. | Spusťte v terminálu `./setup.sh`, nebo jen `python3 .vscode/deska.py vscode`. Pak okno VS Code znovu načtěte (`Ctrl+Shift+P` → *Reload Window*). |
| **`Port COM5 nelze otevřít`** | Port drží jiný program (Serial Monitor, otevřený REPL, graf, Thonny). | Zavřete ho (Serial Monitor odpojte) a příkaz zopakujte. |
| **Po nahrání se program nespustil** | Program vypnul autoreload (`supervisor.runtime.autoreload = False`), nebo je deska v nouzovém režimu. | `cpy check` ukáže příčinu; program spustíte `cpy reset`, nahrávat můžete s `cpy upload --stop`. |
| **Ctrl+S nic nenahraje** | Soubor je v `.vscode/.ignoreCopy`, obsah na desce je stejný, nebo není připojený disk `CIRCUITPY`. | Panel *Output* → *Run On Save*: výpis po krocích ukáže, kde se kopírování zastavilo (`ERROR: v kroku N …` nebo `Konec: …`). Když v panelu není nic, Run on Save se vůbec nespustil – zkontrolujte, že je nainstalované rozšíření *Run on Save* a že má soubor příponu `.py`, `.toml`, `.json`, `.txt` nebo `.csv`. |
