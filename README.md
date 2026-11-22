# Počáteční pracovní adresář pro projekt ve VS Code s Pico:ed

Tento repozitář obsahuje výchozí připravenou strukturu pro vývoj v CircuitPythonu na desce **Pico:ed v2** (Raspberry Pi RP2040) v editoru **Visual Studio Code**.

### Obsah projektu:
- **`.vscode/`** – Konfigurace editoru pro CircuitPython (`settings.json`), doporučená rozšíření (`extensions.json`), pravidla pro ignorování souborů při nahrávání (`.ignoreCopy`) a automatické nahrávací skripty:
  - `copy.ps1` – skript pro Windows (autor Jan Chaloupek)
  - `copy.sh` – skript pro macOS a Linux (autor Robin Bortlík, úprava Jan Chaloupek)
- **`_stubs/`** – Typové stuby a fake moduly CircuitPythonu (`board`, `busio`, `digitalio`, `picoed`, `neopixel`, `pwmio`, `analogio`, `adafruit_ticks`, `time`). Podtržítko v názvu značí, že jde o interní knihovny pro editor a offline unit testy na PC, které se nekopírují do robota. Plně nahrazuje dřívější složku `lib_vsc_only/`.
- **`lib/`** – Složka pro knihovny hardware robota (zrcadlí složku `lib` na disku `CIRCUITPY`).
- **`pyrightconfig.json`** – Konfigurace analyzátoru Pylance/Pyright pro okamžitou nápovědu (IntelliSense) a typovou kontrolu bez falešných chybových hlášení.
- **`code.py`** – Výchozí spouštěný program pro Pico:ed (blikání vestavěné LED).
- **`.gitignore`** – Vyloučení dočasných a systémových souborů z verzování.
