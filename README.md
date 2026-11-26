# Počáteční pracovní adresář pro projekt ve VS Code s Pico:ed (CircuitPython & MicroPython)

Podrobné návody:
- 📘 **[Návod: Práce s MicroPythonem (GUI & CLI)](MicroPython.md)**
- 📙 **[Návod: Práce s CircuitPythonem (GUI & CLI)](CircuitPython.md)**
- 🔧 **[Jak fungují nástroje mpy a cpy (pro zvědavé a pro správce projektu)](Nastroje.md)**

Tento repozitář obsahuje výchozí připravenou strukturu pro vývoj v **CircuitPythonu** (desky Pico:ed v1 a v2) i **MicroPythonu** (Pico:ed v2, BBC micro:bit a Raspberry Pi Pico) v editoru **Visual Studio Code**.

## Rychlý start

1. Otevřete složku projektu ve VS Code.
2. Jednou spusťte **`setup.bat`** (Windows, dvojklikem) nebo **`./setup.sh`** (Linux, macOS).

   > ⚠️ **Na Linuxu a macOS je `./setup.sh` povinný.** Nastavení v `.vscode/settings.json` je připravené pro Windows a spouští nástroje příkazem `python`. Na Linuxu a macOS se Python 3 obvykle jmenuje `python3` a příkaz `python` neexistuje. `./setup.sh` nastavení přepíše na `python3`. Bez něj **nefunguje automatické nahrávání po `Ctrl+S`** ani tlačítka panelu. V panelu *Output* → *Run On Save* pak uvidíte chybu `python: command not found` (nebo `not found`).
   >
   > Po změně v `settings.json` (vlastní úprava, `git pull`) stačí znovu spustit `./setup.sh`, případně jen `python3 .vscode/deska.py vscode`.
3. Připojte desku **datovým** USB kabelem a v terminálu (`Ctrl+~`) zjistěte, co je připojené:
   ```powershell
   .\cpy devices          # Windows PowerShell (na Linuxu: ./cpy.sh devices)
   ```
4. Pracujte podle typu desky:
   - **CircuitPython:** upravte `code.py` a stiskněte `Ctrl+S` – soubor se sám nahraje a spustí.
   - **MicroPython:** upravte `main.py` a klikněte na tlačítko **`MPY ^ Upload`** (nebo `.\mpy upload`), pak `.\mpy reset`.

## Obsah projektu

| Soubor / složka | K čemu je |
|---|---|
| **`code.py`** | výchozí program pro **CircuitPython** (blikání LED, nápis na displeji) |
| **`main.py`** | výchozí program pro **MicroPython** |
| **`lib/`** | knihovny pro desku; `picoed_v2_lib/` je knihovna pro Pico:ed v2 s MicroPythonem (displej, tlačítka, LED, bzučák, ultrazvuk) |
| **`setup.bat`** / **`setup.sh`** | jednorázová příprava prostředí (spustí `.vscode/setup.ps1` / `.vscode/setup.sh`) |
| **`mpy.cmd`** / **`mpy.sh`** | spouštěč nástroje **`mpy`** pro MicroPython |
| **`cpy.cmd`** / **`cpy.sh`** | spouštěč nástroje **`cpy`** pro CircuitPython |
| **`_fake/`** | simulace hardwaru (`board`, `picoed`, `pwmio`, `digitalio`, `neopixel`, `time`, ...) – kód jde spustit na PC bez robota |
| **`_stubs/`** | typové stuby pro nápovědu (IntelliSense) ve VS Code |
| **`pyrightconfig.json`** | nastavení analyzátoru Pylance/Pyright (nápověda bez falešných chyb) |
| **`.gitignore`** | co se neukládá do gitu |

### Složka `.vscode/`

| Soubor | K čemu je |
|---|---|
| **`deska.py`** | **všechny nástroje v jednom souboru**: příkazy `mpy` (MicroPython přes `mpremote`), `cpy` (CircuitPython – přímý zápis na disk `CIRCUITPY`), přehled desek `devices`, graf hodnot `plot` a nastavení panelu `vscode`. Funguje stejně ve Windows, Linuxu i macOS. |
| **`setup.ps1`** / **`setup.sh`** | instalace Pythonu (Windows), knihoven `mpremote` a `matplotlib`, rozšíření VS Code; nastavení panelu a Run on Save |
| **`settings.json`** | nastavení editoru, tlačítek panelu a Run on Save (tlačítka a Run on Save zapisuje `deska.py vscode`) |
| **`extensions.json`** | doporučená rozšíření VS Code |
| **`.ignoreCopy`** | co se **nenahrává** na CircuitPython desku (pro `Ctrl+S` i `cpy upload`) |
| **`upload_config.txt`** | co se **nahrává** na MicroPython desku (`mpy upload`) |
| **`dist/micropython-panel.vsix`** | rozšíření s tlačítky v postranním panelu a ve stavovém řádku |

Dřívější samostatné skripty (`copy.ps1`, `copy.sh`, `upload.ps1`, `list.ps1`, `wipe.ps1`, `repl.ps1`, `utils.ps1`, `ploter.py`, `comStop.py`, ... – celkem 23 souborů) nahradil soubor `deska.py`. Odpovídající příkazy:

| Dříve | Nyní |
|---|---|
| `copy.ps1` / `copy.sh` (Run on Save) | `cpy save <soubor>` |
| `upload.ps1`, `upload_main.ps1`, `run_main.ps1` | `mpy upload`, `mpy main`, `mpy runmain` |
| `repl.ps1`, `list.ps1`, `wipe.ps1`, `check.ps1`, `setup_project.ps1` | `mpy repl`, `mpy list`, `mpy wipe`, `mpy check`, `mpy setup` |
| `ploter.py` | `cpy plot` / `mpy plot` |
| `comStop.py` | `cpy stop` (`--wait` = počká na připojení desky) |
| `zavislosti.bat` | instaluje `setup.bat` |

## Tlačítka v editoru

Rozšíření **MicroPython & CircuitPython Panel** přidá do levého svislého pruhu ikonu čipu. Postranní panel je **rychlý přístup k základním akcím**: má blok **MicroPython** a blok **CircuitPython**. Každý ukazuje připojenou desku (obnovuje se sám) a čtyři tlačítka. Blok, pro který není připojená deska, je ztlumený.

| Blok MicroPython | Blok CircuitPython | Ve stavovém řádku |
|---|---|---|
| ⬆ Nahrát projekt | ⬆ Nahrát projekt | ano (`MPY Upload`, `CPY Upload`) |
| ▶ Spustit main.py | ↻ Restartovat program | |
| ⌨ Konzole (REPL) | ⌨ Konzole (REPL) | ano (`MPY REPL`, `CPY REPL`) |
| 🗑 Smazat desku | 🗑 Smazat desku | – (před smazáním se VS Code zeptá) |

Všechno ostatní (výpis souborů, graf, diagnostika, …) je v terminálu: `.\mpy help`, `.\cpy help`.
