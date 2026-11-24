# Počáteční pracovní adresář pro projekt ve VS Code s Pico:ed (CircuitPython & MicroPython)

Tento repozitář obsahuje výchozí připravenou strukturu pro vývoj v **CircuitPythonu** i **MicroPythonu** na desce **Pico:ed v2** (Raspberry Pi RP2040) a BBC micro:bit v editoru **Visual Studio Code**.

### Obsah projektu:
- **`setup.bat`** / **`.vscode/setup.bat`** – **Jednorázová kompletní příprava prostředí pro studenty** (spustí `.vscode/setup.ps1`):
  - automatická kontrola/instalace Pythonu a pipu
  - instalace nástroje `mpremote` pro MicroPython
  - instalace vestavěného rozšíření `micropython-panel.vsix`
  - hromadná instalace rozšíření z Marketplace (Python, Pylance, CircuitPython, Spell Checker, Indent Rainbow)
  - automatická detekce připojené desky (USB disk CIRCUITPY i COM porty)
- **`.vscode/`** – Konfigurace editoru (`settings.json`), doporučená rozšíření (`extensions.json`), pravidla pro ignorování souborů při nahrávání (`.ignoreCopy`) a nahrávací/ovládací skripty:
  - **CircuitPython podpora:**
    - `copy.ps1` – automatické nahrávání při uložení pro Windows (autor Jan Chaloupek)
    - `copy.sh` – automatické nahrávání pro macOS a Linux (autor Robin Bortlík, úprava Jan Chaloupek)
  - **MicroPython podpora:**
    - `upload.ps1` / `upload_main.ps1` – nahrání projektu na desku přes `mpremote` podle `upload_config.txt`
    - `repl.ps1` – otevření interaktivní konzole MicroPython REPL
    - `list.ps1` – výpis souborů uložených na desce
    - `wipe.ps1` – bezpečné vymazání souborů z desky
    - `mpy.ps1` / `mpy.cmd` – rychlý CLI launcher pro příkazy MicroPythonu
    - `dist/micropython-panel.vsix` – vestavěné rozšíření pro VS Code s tlačítky v Activity Baru i Status Baru
- **`_stubs/`** – Typové stuby pro nápovědu (IntelliSense) a offline testy na PC:
  - CircuitPython: `board`, `busio`, `digitalio`, `picoed`, `neopixel`, `pwmio`, `analogio`, `adafruit_ticks`, `time`
  - MicroPython: `machine`, `rp2`
- **`lib/`** – Složka pro knihovny hardware:
  - `picoed_v2_lib/` – oficiální MicroPython knihovna pro Pico:ed v2 (displej IS31FL3731, tlačítka, neopixel LED, bzučák, ultrazvukový senzor)
- **`pyrightconfig.json`** – Konfigurace analyzátoru Pylance/Pyright pro okamžitou nápovědu bez falešných chybových hlášení.
- **`code.py`** – Výchozí spouštěný program pro CircuitPython (blikání vestavěné LED).
- **`.gitignore`** – Vyloučení dočasných a systémových souborů z verzování.
