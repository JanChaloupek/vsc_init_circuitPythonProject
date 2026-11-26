# Práce s MicroPythonem ve Visual Studio Code (GUI & CLI)

Tato příručka detailně popisuje kompletní vývojový cyklus v **MicroPythonu** v připraveném prostředí editoru Visual Studio Code. Zahrnuje podrobný rozbor hlavního programu **`main.py`** a jeho možností, práci v **grafickém rozhraní (GUI)** i v **příkazové řádce (CLI)**.

---

## 1. Které desky v projektu používají MicroPython

V rámci výuky a tohoto projektu je **MicroPython** určen pro následující hardware:

1. **ELECFREAKS Pico:ed verze 2** (s čipem Raspberry Pi RP2040 a knihovnou `picoed_v2_lib`).
2. **BBC micro:bit verze 1 a verze 2** (využívá oficiální vestavěný modul `microbit`).
3. **Raspberry Pi Pico / Pico W** (využívá oficiální MicroPython firmware a modul `machine`).

> [!NOTE]
> Pro desky **Pico:ed verze 1 a verze 2** je k dispozici také platforma **CircuitPython** (viz samostatný návod `CircuitPython.md`). Desky BBC micro:bit a samostatné Raspberry Pi Pico v tomto kurzu běží výhradně na **MicroPythonu**.

---

## 2. Hlavní program: `main.py` – co dělá a co všechno umí

Soubor **`main.py`** v kořeni projektu je **hlavním vstupním bodem programu pro MicroPython**.

### Jak se `main.py` spouští:
- Mikrokontrolér po připojení napájení, po stisku fyzického tlačítka RESET nebo po odeslání měkkého resetu (`Ctrl+D` v REPL) **vždy automaticky vyhledá a spustí soubor `main.py`**.
- Běží přímo na procesoru mikrokontroléru z interní flash paměti (nebo z RAM při použití rychlého spuštění `mpy runmain`).

---

### Co dělá výchozí starter program v `main.py`:

Výchozí kód je navržen tak, aby po nahrání na desku okamžitě poskytl **vizuální potvrzení, že deska žije, program běží a hardware je v pořádku**:

1. **Automatická detekce desky:**  
   Program bez nutnosti zásahu studenta rozpozná, zda je nahrán na **Pico:ed v2** (použije `picoed_v2_lib`), na **BBC micro:bit** (použije modul `microbit`), na **Raspberry Pi Pico** (použije modul `machine`) nebo zda běží v simulátoru na PC.
2. **Uvítací nápis na displeji:**  
   Ihned po startu zaroluje text **`"ZSaPR"`** na LED matici (17×7 u Pico:ed v2, 5×5 u micro:bitu, textový výpis do konzole u Pico).
3. **Indikátor běhu kódu (Heartbeat):**  
   Vstoupí do hlavní smyčky `while True:`, kde v pravidelném intervalu 0.5 s střídavě zapíná a vypíná stavovou LED diodu. Pokud LED bliká, máte jistotu, že mikrokontrolér nezamrzl a smyčka programu běží.

---

### Co všechno `main.py` umí a jak ho rozšířit pro robota:

Díky připraveným knihovnám v adresáři `lib/picoed_v2_lib/` můžete v `main.py` snadno ovládat veškeré periferie robota:

#### A) Ovládání LED maticového displeje (`Display`)
- **Rolování textu:** `display.scroll("Start zavodu")`
- **Statické zobrazení textu nebo znaku:** `display.show("A")`
- **Vykreslování vlastních obrázků:**
  ```python
  from picoed_v2_lib import Display, Image
  display = Display()
  display.show(Image.HAPPY)   # Zobrazí smajlíka
  ```

#### B) Tlačítka A a B (`Button`)
Tlačítka na přední straně desky slouží pro interakci (např. spuštění jízdy robota po postavení na dráhu):
```python
from picoed_v2_lib import Button
import time

btn_a = Button(Button.A)
btn_b = Button(Button.B)

print("Cekam na stisk tlacitka A pro start...")
while not btn_a.is_pressed():
    time.sleep(0.05)

print("Start! Robot vyrazi vpred!")
```

#### C) Zvuk a tóny bzučáku (`Music`)
Deska obsahuje vestavěný bzučák pro akustickou signalizaci:
```python
from picoed_v2_lib import Music

music = Music()
# Zahraje ton o frekvenci 440 Hz (komorne A) po dobu 200 ms
music.pitch(440, 200)

# Nebo zahraje vestavenou melodii
music.play(Music.BA_DING)
```

#### D) Měření vzdálenosti ultrazvukovým senzorem (`Ultrasonic`)
V knihovně je připraven přímo ovladač ultrazvukového senzoru pro vyhýbání se překážkám:
```python
from picoed_v2_lib.ultrasonic import Ultrasonic
import time

sonar = Ultrasonic()

while True:
    vzdalenost_cm = sonar.read_distance()
    print("Vzdalenost prekazky:", vzdalenost_cm, "cm")
    if vzdalenost_cm < 15:
        print("POZOR PREKAZKA! Zastavit motory!")
    time.sleep(0.2)
```

---

## 3. Jednorázová příprava prostředí (Setup)

Před prvním spuštěním je nutné připravit nástroje a rozšíření v editoru:

- **Na Windows:** dvojklikem spusťte **`setup.bat`** v kořeni projektu.
- **Na Linuxu a macOS:** v terminálu spusťte **`./setup.sh`**. Tady je **povinný**: nastavení je připravené pro Windows (příkaz `python`) a skript ho přepíše na `python3`. Bez něj nefunguje nahrávání po `Ctrl+S` ani tlačítka panelu.

Instalační skript ověří Python 3 (na Windows ho v případě potřeby nainstaluje) a ve složce projektu vytvoří virtuální prostředí **`.venv`**. Do něj nainstaluje nástroj **`mpremote`** (komunikace s deskou, obsahuje i `pyserial`) a **`matplotlib`** (graf hodnot). Dál nainstaluje rozšíření **MicroPython & CircuitPython Panel** a nastaví ovládací tlačítka v editoru. Na konci vypíše, jaké desky jsou připojené.

> 💡 Když `setup.bat` právě nainstaloval Python, **zavřete VS Code a otevřete ho znovu**. Jinak editor nový Python nenajde a tlačítka panelu nefungují.

---

## 4. Práce v grafickém rozhraní VS Code (GUI)

V grafickém rozhraní VS Code je ovládání navrženo pro maximální komfort studentů – veškeré operace jsou dostupné na jedno kliknutí.

Tlačítka přidává rozšíření **MicroPython & CircuitPython Panel** (instaluje ho `setup.bat` / `setup.sh`). Kliknutí na tlačítko otevře integrovaný terminál se jménem `MicroPython` a spustí v něm příkaz.

### A) Postranní panel (Activity Bar)
V levém svislém pruhu klikněte na ikonu čipu **MicroPython & CircuitPython**. Panel je **rychlý přístup k základním akcím**. Má dva bloky, **MicroPython** a **CircuitPython**, a každý ukazuje:

- **připojenou desku** té platformy – port (např. `COM4`) a jméno desky. Seznam se sám obnovuje každých 5 s, dokud je panel vidět; tlačítkem **↻** nahoře ho obnovíte hned. Sériové porty se při tom neotevírají, takže to nevadí běžícímu REPL ani Serial Monitoru.
- **čtyři základní tlačítka**.

Když žádná deska té platformy připojená není, je blok ztlumený (tlačítka ale fungují dál). Tlačítka bloku MicroPython:

| Tlačítko | Co udělá |
|---|---|
| **⬆ Nahrát projekt** *(žluté)* | nahraje soubory podle `upload_config.txt` na desku (`mpy upload`) |
| **▶ Spustit main.py** *(zelené)* | restartuje desku, takže se spustí nahraný `main.py` (`mpy reset`) |
| **⌨ Konzole (REPL)** *(modré)* | otevře interaktivní Python konzoli na desce (`mpy repl`) |
| **🗑 Smazat desku** *(červené)* | smaže všechny soubory na desce – VS Code se nejdřív zeptá v dialogu (`mpy wipe`) |

Další příkazy (výpis souborů, diagnostika, graf, …) jsou v terminálu – viz kapitola 5 a `.\mpy help`. Panel na ně odkazuje dole.

### B) Spodní stavový řádek (Status Bar)
Ve stavovém řádku jsou s ikonami jen nejčastější akce: **`MPY Upload`**, **`MPY REPL`**, **`CPY Upload`** a **`CPY REPL`**.

### C) Paleta příkazů (Command Palette)
Stiskněte **`Ctrl+Shift+P`** (nebo klávesu **`F1`**) a napište `MicroPython & CircuitPython: Commands` – otevře se rychlá nabídka všech akcí rozdělená podle skupin. Příkaz `… Open Panel` otevře panel jako záložku v editoru.

---

## 5. Práce v příkazové řádce (CLI)

Pro rychlé ladění a skriptování je v terminálu VS Code (`Ctrl+~`) k dispozici nástroj **`mpy`**:

- **Windows – PowerShell** (výchozí terminál ve VS Code): `.\mpy <příkaz>`
  (PowerShell nespouští programy z aktuální složky bez `.\` na začátku)
- **Windows – příkazový řádek cmd:** `mpy <příkaz>`
- **Linux a macOS:** `./mpy.sh <příkaz>`
- **Kdekoliv:** `python .vscode/deska.py mpy <příkaz>` (takhle příkazy volá panel)

Deska se najde sama. Když je jich připojeno víc, vyberete ji volbou `--port COMx`.

**Podrobný výpis:** příkazy, které spouštějí tlačítka panelu (`upload`, `main`, `reset`, `repl`, `wipe`), vypisují očíslované kroky – co se nahrává, která deska a jestli odpovídá, co dělá `mpremote`, kolik souborů se nahrálo a kolik bylo beze změny, první výstup programu po spuštění. Když se něco nepovede, poslední řádek řekne, ve kterém kroku a co s tím:

```text
2) Deska s MicroPythonem
   port:        COM4
ERROR: v kroku 2 - port COM4 je obsazeny jinym programem.
       - neni otevreny REPL v jinem okne?
```

### A) Příkazy nástroje `mpy`

```bash
# Zobrazení nápovědy
mpy help

# 1. Nahrání celého projektu podle upload_config.txt
#    (nezměněné soubory mpremote přeskočí - vypíše "Up to date")
mpy upload

# 2. Rychlé nahrání POUZE souboru main.py
mpy main

# 3. Spuštění main.py přímo z paměti RAM bez zápisu do flash
#    (extrémně rychlé pro testování drobných úprav v algoritmu; jde i jiný soubor)
mpy runmain
mpy runmain test_motoru.py

# 4. Otevření interaktivní REPL konzole (ukončení Ctrl+])
mpy repl

# 5. Přehledný stromový výpis souborů na desce včetně jejich velikostí
mpy list

# 6. Kompletní smazání všech souborů z desky (zeptá se; -y = bez otázky)
mpy wipe

# 7. Diagnostika: odpověď desky, verze firmwaru, volné místo a paměť, soubory
mpy check

# 8. Kompletní příprava nové desky (Wipe -> Upload -> List)
mpy setup

# 9. Restart desky - spustí nahraný main.py (--hard = jako tlačítko RESET)
mpy reset

# 10. Živý graf hodnot, které program vypisuje přes print() (viz B)
mpy plot

# 11. Jaké desky jsou připojené (MicroPython i CircuitPython)
mpy devices
```

> [!IMPORTANT]
> Na rozdíl od CircuitPythonu se u MicroPythonu program po nahrání **nespustí sám**. Spusťte ho příkazem `mpy reset`, tlačítkem RESET na desce, nebo v REPL klávesou `Ctrl+D`.

### B) Živý graf hodnot (`mpy plot`)
Program na desce vypisuje čísla oddělená čárkou – první číslo je osa X (např. čas), další čísla jsou křivky:

```python
import time
start = time.ticks_ms()
while True:
    cas = time.ticks_diff(time.ticks_ms(), start) / 1000
    print(cas, vzdalenost, rychlost)
    time.sleep(0.05)
```

Program nahrajte a spusťte (`mpy main`, `mpy reset`), pak spusťte `mpy plot`. Řádky, které nejsou čísla, graf přeskočí. Graf ukončíte zavřením okna.

### C) Přímé volání nástroje `mpremote` (Power User CLI)
`mpy` uvnitř používá nástroj `mpremote`. Ten můžete volat i přímo:

```bash
# Seznam připojených desek a jejich portů
python -m mpremote devs

# Výpis souborů na desce
python -m mpremote ls
python -m mpremote ls :lib

# Zkopírování jednoho souboru na desku
python -m mpremote cp senzor.py :

# Stažení souboru z desky do PC
python -m mpremote cp :namerena_data.txt zaloha.txt

# Spuštění jednoho řádku kódu
python -m mpremote exec "import machine; print(machine.unique_id())"

# Restart desky (jako tlačítko RESET)
python -m mpremote reset
```

> [!NOTE]
> `python -m mpremote soft-reset` restartuje desku z takzvaného *raw REPL* a v tom režimu MicroPython `main.py` **nespustí**. Pro spuštění programu použijte `mpy reset`.

Jak nástroj funguje uvnitř, popisuje **[Nastroje.md](Nastroje.md)**.

---

## 6. Klávesové zkratky v REPL konzoli

- **Ukončení REPL:** **`Ctrl+]`** (případně `Ctrl+X`).  
  *Důležité: Nikdy nezavírejte okno terminálu křížkem bez ukončení REPL, jinak port zůstane uzamčený na pozadí!*
- **Přerušení běžícího programu:** **`Ctrl+C`**.
- **Měkký restart (Soft Reset):** **`Ctrl+D`** (znovu inicializuje MicroPython a spustí `main.py`).
- **Režim vkládání víceřádkového kódu (Paste Mode):** **`Ctrl+E`** → vložte kód → **`Ctrl+D`**.

---

## 7. Konfigurace nahrávání (`upload_config.txt`)

Soubor `.vscode/upload_config.txt` definuje položky přenášené příkazem `upload`:
```text
# Seznam souborů a adresářů k uploadu na MicroPython zařízení
main.py
lib
```
Chcete-li do robota nahrát další modul (např. `motory.py` nebo `nastaveni.json`), přidejte jeho název na nový řádek.

---

## 8. Offline vývoj a simulace (`_fake` a `_stubs`)

- Složka **`_fake/`** obsahuje simulaci hardware (`board`, `picoed`, `digitalio`, `neopixel`).
- Kód `main.py` můžete spustit přímo na počítači bez připojené desky:
  ```bash
  python main.py
  ```
- Složka **`_stubs/`** v kombinaci s `pyrightconfig.json` poskytuje kompletní našeptávání metod a typovou kontrolu (Pylance).

---

## 9. Řešení častých potíží (Troubleshooting)

| Problém | Příčina | Řešení |
|---|---|---|
| **ERROR: Zarizeni nereaguje / Port je uzamcen** | Port drží otevřený jiný proces (REPL v jiném okně, Thonny apod.). | Zavřete všechny panely terminálu ve VS Code tlačítkem koše. Odpojte a znovu připojte USB kabel. |
| **Deska zamrzla v nekonečném cyklu while True** | Smyčka běží bez `time.sleep()`, mikrokontrolér nestíhá obsluhu USB. | Otevřete REPL a stiskněte opakovaně `Ctrl+C`. Poté spusťte `mpy wipe`. |
| **mpremote: command not found** | Python nebo mpremote chybí v systémové cestě PATH. | Spusťte znovu `setup.bat` (nebo `setup.sh`), který prostředí zkontroluje a nastaví. |
| **`NameError: name '\ufeff...' isn't defined` na 1. řádku** | Soubor je uložený jako „UTF-8 with BOM“ (neviditelná značka na začátku, přidává ji např. Poznámkový blok). | `mpy upload` na to upozorní. Ve VS Code klikněte vpravo dole na `UTF-8 with BOM` → `Save with Encoding` → `UTF-8` a nahrajte znovu. |
| **Po nahrání se nic neděje** | MicroPython po nahrání program nespouští. | Spusťte ho: `mpy reset` (nebo tlačítko RESET). |
| **MicroPython deska nenalezena** | Deska není připojená datovým kabelem, nebo je na ní CircuitPython. | `mpy devices` ukáže, co je připojené; na CircuitPython použijte `cpy`. |
