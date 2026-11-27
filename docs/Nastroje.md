# Jak fungují nástroje `mpy` a `cpy`

Tento návod je pro zvědavé studenty a pro toho, kdo bude projekt upravovat. Popisuje, co se děje „pod kapotou“, když stisknete tlačítko v panelu nebo napíšete `cpy upload`. Pro běžnou práci stačí [MicroPython.md](MicroPython.md) a [CircuitPython.md](CircuitPython.md).

---

## 1. Jeden soubor pro všechno: `.vscode/deska.py`

Všechny nástroje jsou v jediném Python souboru **`.vscode/deska.py`**. Spouští se třemi způsoby, které dělají totéž:

| Jak | Příklad | Kdo to používá |
|---|---|---|
| spouštěč ve Windows | `.\cpy upload` (PowerShell), `cpy upload` (cmd) | student v terminálu |
| spouštěč v Linuxu / macOS | `./cpy.sh upload` | student v terminálu |
| přímo Pythonem | `python .vscode/deska.py cpy upload` | panel, Run on Save, setup |

Spouštěče `mpy.cmd`, `cpy.cmd`, `mpy.sh` a `cpy.sh` mají jen pár řádků: zavolají `deska.py` a řeknou mu, jestli jde o `mpy`, nebo `cpy`.

**Proč Python, a ne PowerShell a bash?**
- Jeden soubor funguje ve Windows, Linuxu i macOS. Dřív byla každá věc napsaná dvakrát (`.ps1` a `.sh`) a obě verze se postupně rozcházely.
- Python je potřeba stejně – `mpremote`, `pyserial`, `python-minifier` i `matplotlib` jsou Python knihovny.
- Odpadají potíže PowerShellu: zakázané spouštění skriptů (*ExecutionPolicy*) na školních počítačích nebo neviditelná značka BOM v dočasných souborech.

Jen **`setup.ps1`** a **`setup.sh`** zůstaly v PowerShellu a bashi, protože musí umět nainstalovat samotný Python. `setup.ps1` ho na Windows nainstaluje jen pro uživatele (bez administrátora). `setup.sh` na Linuxu potřebuje systémový správce balíčků a `sudo`, proto nejdřív vypíše příkaz a zeptá se (`[a/N]`); bez terminálu nebo po odpovědi `n` příkaz jen vypíše. Na Ubuntu/Debianu doinstaluje i chybějící `python3.X-venv`.

### Knihovny ve virtuálním prostředí `.venv`

`setup.bat` / `setup.sh` instalují knihovny (`mpremote`, `pyserial`, `python-minifier`, `matplotlib`) do složky **`.venv`** v kořeni projektu, ne do systémového Pythonu:
- Novější Linuxy (Ubuntu 23.04+, Debian 12+) instalaci přes `pip` mimo virtuální prostředí odmítají (chyba `externally-managed-environment`).
- Každý projekt má své knihovny a systémový Python zůstane čistý. Cena je asi 140 MB na projekt (hlavně `matplotlib` a `numpy`).

Příkazy v panelu, Run on Save i spouštěče dál volají obyčejné `python .vscode/deska.py …` (na Linuxu a macOS `python3`). `deska.py` si `.venv` najde sám:
- `.venv` vzniklo ze stejného Pythonu, který právě běží (běžný případ): přidá si jeho knihovny do cesty, kde Python hledá moduly. Je to rychlé, nespouští se žádný další proces.
- `.venv` vzniklo z jiného Pythonu: spustí se znovu Pythonem z `.venv`.
- `.venv` neexistuje: použijí se knihovny systémového Pythonu (projekty připravené dřívější verzí setupu).
- `.venv` je rozbité (Python, ze kterého vzniklo, byl odinstalovaný): `deska.py` vypíše upozornění a pokračuje bez něj. `setup.bat` / `setup.sh` takové `.venv` pozná a vytvoří znovu.

Automatická aktivace `.venv` v terminálu je v `.vscode/settings.json` vypnutá (`python.terminal.activateEnvironment: false`, `python-envs.terminal.autoActivationType: off`). `deska.py` ji nepotřebuje a rozšíření Python by aktivační příkaz poslalo do terminálu i s Ctrl+C. Tím by přerušilo právě běžící `setup.bat` (dotaz *Terminate batch job (Y/N)?*): setup vytvoří `.venv` a hned potom nainstaluje rozšíření Python do otevřeného okna, které se okamžitě aktivuje. Pylance si `.venv` jako interpret vybere i tak.

Další knihovnu (např. `circup` pro `cpy lib`) nainstalujete do `.venv` takto: `.venv\Scripts\python -m pip install circup` (Windows), `.venv/bin/python -m pip install circup` (Linux, macOS).

Soubor `deska.py` je rozdělený na oddíly (v kódu hledejte `ODDIL`):

| Oddíl | Obsah |
|---|---|
| 1 | nastavení, tabulka desek podle VID:PID |
| 2 | výpis na obrazovku (barvy, hlášky, potvrzování) |
| 3 | hledání desek: USB disky a sériové porty, uložený výběr desky (`select`) |
| 4 | sériová konzole desky – REPL a raw REPL |
| 5 | soubory projektu (`.ignoreCopy`), BOM, stromový výpis |
| 6 | společné příkazy: `devices`, `vscode`, graf |
| 7 | CircuitPython – příkazy `cpy`; na konci simulace a testy na PC pro obě platformy (`pc_hardware`, `pc_sim`, `pc_test`) |
| 8 | MicroPython – příkazy `mpy` |
| 9 | nápověda, čtení parametrů, hlavní funkce |

---

## 2. Jak se najde deska

Každé USB zařízení má dvě čísla: **VID** (výrobce) a **PID** (výrobek), např. `2E8A:1026`. Podle nich `deska.py` pozná, o jakou desku jde (tabulky `CP_DEVICES` a `MP_DEVICES` v oddílu 1). Příkaz `devices` vypíše všechno, co je připojené:

```text
CircuitPython  (prikazy cpy)
   COM5     disk F:\   Adafruit CircuitPython 9.2.7 on 2025-04-01; ELECFREAKS PICO:ED with rp2040
MicroPython  (prikazy mpy)
   COM4     Raspberry Pi Pico / Pico W (MicroPython)   (USB 2E8A:0005)
```

**Deska s CircuitPythonem** má v počítači dvě části: USB disk **`CIRCUITPY`** a sériový port (např. `COM5`). Patří k sobě, protože číslo **UID** v souboru `boot_out.txt` na disku je stejné jako sériové číslo USB portu. Díky tomu `cpy` správně spáruje disk s portem, i když je ve třídě připojeno víc desek.

**Deska s MicroPythonem** má jen sériový port. Najde se podle VID:PID.

### Verze desky Pico:ed (v1 / v2)

Pico:ed v1 a v2 mají stejné USB VID:PID (`2E8A:1026`) i stejný firmware (`Board ID:elecfreaks_picoed` v `boot_out.txt`), takže je bez spuštění kódu na desce rozlišit nejde. Liší se zapojením pinů GP0 a GP1:

| | v1 | v2 |
|---|---|---|
| GP0 / GP1 | bzučák na GP0 (`board.BUZZER_GP0`), bez pull-up rezistorů | vnitřní sběrnice I2C displeje (`board.I2C0_SDA` / `I2C0_SCL`) s pull-up rezistory |
| displej IS31FL3731 (adresa `0x74`) | na sběrnici okraje P19 / P20 (`board.SCL` / `SDA`) | na GP0 / GP1 |
| bzučák | GP0 | GP3 (`board.BUZZER`) |

`deska.py` proto na desce na chvíli nastaví GP0 a GP1 jako vstup s vnitřním pull-down a přečte je (`PICOED_HW_SNIPPET`): obě 1 = pull-upy = **v2**, jinak **v1**. Nic se neposílá po sběrnici a bzučák mlčí. Program na desce přitom musí stát, proto se verze zjišťuje jen v příkazech, které program zastavují tak jako tak – `cpy check`, `cpy reset` (tlačítko *Restartovat program*), `cpy repl` a příkazy s `--stop` – a jen jednou: výsledek se uloží k UID desky do souboru `hw_desek.json` u uživatele (Windows `%LOCALAPPDATA%\deska`, Linux a macOS `~/.cache/deska`), ne do projektu – deska svou verzi nezmění a používá se v různých projektech.

`devices` (a tedy i panel) verzi jen čte z tohoto souboru, port neotevírá: u desky vypíše `(HW v1)` / `(HW v2)` a v `devices --json` pole `hw`. U desky, jejíž verze ještě není známá, je poznámka, jak ji zjistit. UID je zároveň sériové číslo USB portu, takže verzi pozná i deska přehraná na MicroPython (`ELECFREAKS Pico:ed (MicroPython) (HW v2)`).

### Víc desek stejného druhu

Bez dalšího nastavení se použije první nalezená deska. Jinou vyberete třemi způsoby:

| Jak | Příklad | Platí |
|---|---|---|
| příkaz `select` | `mpy select COM4`, `cpy select F:` nebo `cpy select COM5`; bez parametru nabídne očíslovaný seznam | natrvalo, dokud nenapíšete `select auto` |
| kliknutí na desku v panelu | panel na pozadí zavolá `deska.py mpy select COM4` / `cpy select COM5` | natrvalo; dalším kliknutím na vybranou desku se volba zruší |
| volba příkazu | `--port COMx`, u CircuitPythonu i `--drive F:` | jen pro tento příkaz, má přednost před uloženým výběrem |

Uložená volba je v souboru `.vscode/.active_device.json` (je v `.gitignore` – každý počítač má svou). U CircuitPythonu stačí uložit disk, nebo port: druhou část `cpy` dohledá podle UID (panel ukládá port). Když uložená deska není připojená, použije se zase první nalezená.

`devices` u ručně vybrané desky vypíše `[vybrana rucne]`, a když je desek víc, u té, která se použije bez výběru, `[vychozi aktivni]`. V `devices --json` má každá deska pole `active` (s touto deskou se pracuje) a `selected` (vybraná ručně) – podle nich panel kreslí ● a ○.

---

## 3. CircuitPython: zápis na disk a autoreload

CircuitPython po startu spustí **`code.py`** (když chybí, tak `main.py`). Když se na disk `CIRCUITPY` něco zapíše, CircuitPython **počká, až zápisy na chvíli ustanou, a program jednou restartuje**. Tomu se říká *autoreload*.

Proto `cpy upload` i `Ctrl+S` kopírují soubory **přímo na disk** a o spuštění se postará sám CircuitPython. Ověřili jsme to měřením na desce Pico:ed (CircuitPython 9.2.7):

| Jak se kopírovalo | Restartů programu |
|---|---|
| 6 souborů rychle za sebou (jako `cpy upload`) | **1** – až po posledním souboru |
| 4 soubory s mezerou 0,3 s | **1** |
| 4 soubory s mezerou 1 s (ruční kopírování) | **4** – po každém souboru |

Z toho plyne:
- `cpy upload` kopíruje rychle za sebou a **`code.py` jako poslední**, takže program se nikdy nespustí s napůl nahranými soubory.
- Kopírují se jen soubory, které se liší od desky. Uložení nezměněného souboru program zbytečně nerestartuje.
- **Práce se soubory (`save`, `upload`, `main`, `list`, `wipe`, `setup`) sériový port vůbec nepoužívá.** Proto funguje i s otevřeným Serial Monitorem nebo REPL v jiném okně a výstup nového programu je rovnou vidět v monitoru.
- Volba **`--watch`** po zápisu sériový port **jen poslouchá** (nic neposílá) a ukáže, jestli se program spustil a co vypsal – včetně chyby. Port musí být volný.
- Volba **`--stop`** program před zápisem zastaví a pak ho jednou spustí. Hodí se pro velká nahrávání a pro desku, na které program vypnul autoreload (`supervisor.runtime.autoreload = False`) – `cpy check` na to upozorní.
- Sériový port potřebují jen příkazy, které s deskou mluví: `repl`, `runmain`, `monitor`, `plot`, `stop`, `reset`, `check`, `wipe --format`, `bootloader`.

---

## 4. Sériová konzole: REPL a raw REPL

Některé věci přes disk udělat nejdou – zastavit program, otevřít konzoli, spustit kód bez zápisu na disk. K tomu slouží sériová linka. MicroPython i CircuitPython jí rozumějí stejně:

| Klávesa (bajt) | Co udělá |
|---|---|
| `Ctrl+C` (0x03) | přeruší běžící program |
| `Ctrl+D` (0x04) | v REPL: měkký restart – znovu spustí `code.py` / `main.py` |
| `Ctrl+A` (0x01) | přepne do **raw REPL** – režimu pro programy |
| `Ctrl+B` (0x02) | zpět z raw REPL do normálního REPL (výzva `>>> `) |

**Jak `cpy runmain` spustí program z RAM** (bez zápisu na disk):
1. `Ctrl+C` zastaví běžící program, `Ctrl+B` přepne do normálního REPL (deska odpoví `>>> `).
2. `Ctrl+A` přepne do raw REPL (deska odpoví `raw REPL; CTRL-B to exit` a `>`).
3. Pošle se text programu (po 256 bajtech, aby deska stíhala) a `Ctrl+D` ho spustí.
4. Deska odpoví `OK`, pak posílá výstup programu, znak 0x04, chybový výstup, znak 0x04 a výzvu `>`.
5. `Ctrl+B` vrátí desku do normálního REPL.

Program spuštěný z RAM si moduly, které importuje (např. `robot.py`), načítá **z desky**. Proto `cpy runmain` upozorní, když jsou na desce jejich starší verze.

CircuitPython navíc posílá sekvence `ESC ] 0 ; ... ESC \`, kterými mění titulek okna terminálu. Do výpisu nepatří, proto je `deska.py` odfiltruje (třída `OscFilter`).

Ladění: s proměnnou prostředí `CPY_DEBUG=1` se vypisuje všechno, co jde po sériové lince tam (`[tx]`) i zpět (`[rx]`):
```powershell
$env:CPY_DEBUG = "1"; .\cpy check; Remove-Item Env:CPY_DEBUG
```

---

## 5. MicroPython: nástroj `mpremote`

MicroPython deska nemá USB disk, takže `mpy` všechno dělá přes nástroj **`mpremote`** (`python -m mpremote`):

| `mpy` | co zavolá |
|---|---|
| `mpy upload`, `mpy main` | `mpremote connect COM4 cp main.py : + cp -r lib :` – víc příkazů spojených `+` v jednom spojení |
| `mpy runmain` | `mpremote connect COM4 run main.py` |
| `mpy repl` | `mpremote connect COM4 repl` – `Ctrl+C` je v konzoli obyčejná klávesa (`ctrl_c_as_key`), ne signál. Jinak by ho dostal i `cmd.exe`, ve kterém běží `mpy.cmd`, a po konci konzole by se ptal *Terminate batch job (Y/N)?* |
| `mpy list`, `mpy wipe`, `mpy check` | `mpremote connect COM4 exec "<krátký program>"` – program na desce projde soubory a vypíše je jako JSON |
| `mpy reset --hard` | `mpremote connect COM4 reset` |
| `mpy reset` | přímo po sériové lince: `Ctrl+C`, `Ctrl+B`, `Ctrl+D` |

> [!WARNING]
> `mpremote soft-reset` restartuje desku z raw REPL a v tom režimu MicroPython **nespustí `main.py`**. Proto `mpy reset` posílá `Ctrl+D` z normálního REPL. Na tuhle past jsme narazili při testování.

`mpremote cp` porovnává obsah souborů a nezměněné přeskočí (vypíše `Up to date`).

Soubory se kopírují s cílovým jménem (`cp main.py :main.py`, ne jen `cp main.py :`). BBC micro:bit by je jinak uložil pod **prázdné jméno**.

**BBC micro:bit** (USB `0D28:0204`, tabulka `MP_FLAT_USB`) má ploché úložiště: bez složek, bez `os.mkdir`, bez modulu `json`, a `os.listdir()` u něj nebere cestu. Proto:
- `mpy upload` místo `cp -r lib :` kopíruje soubory ze složky po jednom do kořene a podsložky přeskočí (`mp_cp_plan`).
- `mpy list`, `wipe` a `check` posílají na desku kód, který vypíše seznam souborů jako zápis Pythonu (`repr`), ne jako JSON. Na PC ho načte `ast.literal_eval`.
- Ostatní příkazy (`reset`, `repl`, `runmain`) fungují stejně jako u Pica.
- `mpremote` po každém příkazu raw REPL opouští (`Ctrl+B`), ale micro:bit tento poslední znak často nedostane: port se zavře dřív, než ho převodník na desce předá (naměřeno asi 4 z 6 pokusů). Konzole by pak místo `>>>` ukázala `OK>` a nereagovala. Proto `mpy repl` před spuštěním `mpremote repl` pošle `Ctrl+B` sám a chvíli počká (`mp_leave_raw_repl`).
- `mpy list` a `mpy check` odhadnou zaplnění úložiště (`microbit_space_text`: bloky po 128 B, z nich 126 B dat, celkem asi 20 160 B u v2).

Proč to tak je a naměřená čísla: [MicroBit.md](MicroBit.md).

**Když `mpremote` selže**, funkce `mp_failure` z jeho výstupu pozná příčinu (tabulka `MP_FAILURES`: místo, RAM, obsazený port, deska neodpovídá, chyba přenosu, přerušené spojení). Před opakováním ji vypíše a opakuje (nejvýš `MP_RETRIES` = 2×) jen to, co má smysl: chybu přenosu (`SyntaxError` v kódu, který `mpremote` sám poslal – na micro:bitu asi 3 % příkazů), přerušené spojení a zablokovaný raw REPL. Opakují se jen interní příkazy (`exec`, `cp`, `ls`, `rm` – tabulka `MP_RETRY_CMDS`), ne `run` s programem studenta.

---

## 6. Co se nahrává: `.ignoreCopy` a `upload_config.txt`

Obě platformy mají vlastní soubor, protože se nahrávají jinak:

| | CircuitPython | MicroPython |
|---|---|---|
| soubor | `.vscode/.ignoreCopy` | `.vscode/upload_config.txt` |
| princip | co se **ne**nahrává (výjimky) | co se nahrává (seznam) |
| použije | `Ctrl+S` (Run on Save), `cpy upload`, `cpy setup` | `mpy upload`, `mpy setup` |

V `.ignoreCopy` je jedna maska na řádek: `*` znamená „cokoliv“ i přes více složek, `**` totéž. Řádky začínající `#` jsou komentáře. Skryté položky (`.git`, `.vscode`), `__pycache__`, `*.pyc` a `boot_out.txt` se nekopírují nikdy. Soubor sám obsahuje vysvětlení ke každé masce.

Run on Save reaguje na soubory `.py`, `.toml`, `.json`, `.txt` a `.csv` (nastavení `RUN_ON_SAVE_MATCH`). Binární soubory (`.mpy`, `.bmp`, `.wav`) se v editoru neukládají, takže je Run on Save nezachytí – na ně je `cpy upload`.

---

## 7. Neviditelná značka BOM

Některé editory (Poznámkový blok, PowerShell) ukládají soubory jako **„UTF-8 with BOM“** – na začátek přidají 3 neviditelné bajty. MicroPython ani CircuitPython je neznají a program spadne hned na 1. řádku:

```text
NameError: name '\ufeff' is not defined
```

- `cpy` značku při kopírování z `.py` souborů odstraní sám a upozorní na to.
- `mpy upload` kopíruje přes `mpremote` beze změny, proto na soubory s BOM jen upozorní. `mpy runmain` pošle vyčištěnou kopii.
- Natrvalo: ve VS Code klikněte vpravo dole ve stavovém řádku na `UTF-8 with BOM` → `Save with Encoding` → `UTF-8`.

---

## 8. Tlačítka panelu a Run on Save

Panel (rozšíření *MicroPython & CircuitPython Panel*, zdrojový kód v repozitáři `micropython-panel`) bere z `.vscode/settings.json`:

| Nastavení | Co obsahuje |
|---|---|
| `micropython.commands` | tlačítka: `id`, `name` (text ve stavovém řádku, může mít ikonu `$(play)`), `label` (text v panelu), `command` (příkaz do terminálu), `color`, `group` (blok v panelu), `platform` (`micropython` / `circuitpython` – které desky blok ukazuje; bez připojené desky se ztlumí; blok bez `platform` – *Na PC bez desky* – desky neukazuje a neztlumí se), `statusBar` (`false` = jen v panelu) |
| `micropython.devicesCommand` | příkaz pro seznam připojených desek: `python .vscode/deska.py devices --json` |
| `micropython.devicesRefreshSeconds` | jak často seznam obnovovat, když je panel vidět (výchozí 5 s) |
| `emeraldwalk.runonsave` | Run on Save: `python .vscode/deska.py cpy save "${relativeFile}"` |

Každé tlačítko jen vloží text příkazu do terminálu `MicroPython`. Seznam desek rozšíření nezjišťuje samo – spouští `devicesCommand` (jen když je panel vidět) a čte jeho JSON. `deska.py devices --json` přitom sériové porty neotevírá, takže nevadí běžícímu REPL ani Serial Monitoru. Když je v bloku víc desek, jsou klikací. Kliknutí nejde do terminálu: panel spustí `deska.py mpy|cpy select` na pozadí a seznam obnoví (viz [Víc desek stejného druhu](#víc-desek-stejného-druhu)).

Všechna tato nastavení **zapisuje příkaz `python .vscode/deska.py vscode`** (volá ho setup). Tlačítka jsou tak definovaná na jediném místě – v seznamu `PANEL_BUTTONS` v oddílu 6 souboru `deska.py`. Rozdíl mezi systémy je jen jeden: Windows volají `python`, Linux a macOS `python3`.

Panel je záměrně **rychlý přístup k základním akcím** (nahrát, spustit / restartovat, konzole, smazat desku; na PC simulace a testy) – ne kopie všech příkazů CLI. Nevratné akce mají 8. položku `confirm` – otázku, kterou VS Code položí v dialogu; příkaz pak má `--yes`, aby se terminál neptal podruhé. Ostatní příkazy jsou v terminálu (`mpy help`, `cpy help`). Než přidáte tlačítko, zvažte, jestli ho studenti opravdu potřebují často.

**Jak přidat tlačítko** (např. zastavení programu na CircuitPythonu):
1. V `deska.py` přidejte do `PANEL_BUTTONS` řádek (id, text ve stavovém řádku, text v panelu, příkaz `deska.py`, barva, blok, ve stavovém řádku?):
   ```python
   ("cpy-stop", "$(debug-stop) CPY Stop", "\u25a0  Zastavit program", "cpy stop", "orange", _CPY, False),
   ```
   (`deska.py` je čisté ASCII, proto se české znaky a symboly píšou jako `\u00e1` (á) apod.)
2. Spusťte `python .vscode/deska.py vscode`.
3. VS Code nabídne **Přenačíst okno** (nebo `F1` → `Developer: Reload Window`).

Ostatní položky v `settings.json` (kontrola pravopisu, ...) příkaz `vscode` nemění.

### Zmenšení souborů: `mpy minify` / `cpy minify`

Jeden přepínač se stavy `off`, `simple`, `full` a (jen pro `mpy`) `max`, zvlášť pro `mpy` a `cpy`. Nastavení je v **`.vscode/deska.json`** (patří do gitu, učitel ho může v šabloně přednastavit):

```json
{
    "minify": {"mpy": "simple", "cpy": false},
    "minify_keep": ["jmeno_ktere_se_neprejmenuje"],
    "minify_exclude": ["lib/robot.py"]
}
```

- Zmenšuje knihovna `python-minifier` (povinná, instaluje ji setup) s volbami z `MINIFY_LEVELS`: `simple` odstraní komentáře, dokumentační řetězce a mezery; `full` navíc přejmenuje lokální proměnné a vytáhne opakované konstanty. Globální jména (třídy, funkce) se nepřejmenují nikdy, protože je importují jiné soubory. Jména z `minify_keep` (`minify keep` / `unkeep`) zůstanou vždy.
- `main.py`, `code.py` a `boot.py` se nezmenšují (`NO_MINIFY`) – čísla řádků v chybách programu studenta musí sedět. Další soubory vyřadí `minify exclude <vzory>` (`minify_exclude`, funkce `minify_excluded`; vzory jako v `.ignoreCopy`).
- **`max`** (`mp_merge_program`): přes modul `ast` projde `main.py` a místní moduly, které importuje (`from modul import ...`, soubory v kořeni a v `lib/`), a sloučí je v pořadí podle závislostí. Importy cizích modulů dá nahoru (bez duplicit), `from m import a as b` nahradí přiřazením `b = a` a vynechá bloky `if __name__ == "__main__":` importovaných modulů. Odmítne `import modul`, `import *`, vnořené a relativní importy, kruhy a kolize jmen. Výsledek zmenší s `rename_globals=True`. Jednotlivé soubory se při `max` zmenšují jako `full`.
- Nahrávání vždy vypíše nastavení (`minify_report`): vypnuto = jeden řádek, zapnuto = úroveň a seznam, co se zmenší a co ne (a proč).
- **CircuitPython:** zmenšení je ve funkci `board_bytes()` – tu používá porovnání s deskou (`same_content`) i zápis (`copy_file`), takže `cpy upload` i `cpy save` (Run on Save) porovnávají zmenšený obsah a nezměněné soubory dál přeskočí.
- **MicroPython:** `mp_stage()` připraví do dočasné složky kopii nahrávaných položek se zmenšenými `.py` soubory a `mpremote` nahrává z ní. Jeho porovnání (`Up to date`) tak funguje stejně.
- Soubor, který zmenšit nejde (např. chyba v syntaxi), se nahraje beze změny a `deska.py` na to jednou upozorní.

### Nápověda Pylance: `pyrightconfig.json`

Kde Pylance hledá moduly, je v souboru **`pyrightconfig.json`** v kořeni projektu (`extraPaths`: `lib`, `pc/_stubs`, `pc`; `stubPath`: `pc/_stubs`; vypnuté hlášení `reportMissingModuleSource`). V `settings.json` to být nemůže, protože rozšíření CircuitPython (`wmerkens.vscode-circuitpython-v2-cursor-ai`) při každém otevření projektu a po výběru desky přepíše `python.analysis.extraPaths`: na první dvě místa dá absolutní cesty do svého adresáře v profilu uživatele a naše `./lib` tím zmizí. Když `pyrightconfig.json` existuje, Pylance nastavení `python.analysis.*` ze `settings.json` ignoruje, takže přepsání nápovědě nevadí.

Rozšíření do `settings.json` zapisuje dál – při každé aktivaci `python.languageServer` a `python.analysis.diagnosticSeverityOverrides` (ty jsou v souboru už předem, aby se nic neměnilo), po výběru desky `circuitpython.board.*` a `python.analysis.extraPaths`. **Řádek `python.analysis.extraPaths` s cestami do profilu necommitujte** – patří jen na váš počítač.

---

## 9. Jak přidat nový příkaz

1. Napište funkci v oddílu 7 (CircuitPython, parametry `board, opts`) nebo 8 (MicroPython, parametr `opts`). Na začátek dejte docstring – co příkaz dělá.
2. Přidejte ji do tabulky `CPY_COMMANDS` nebo `MPY_COMMANDS` (oddíl 9) spolu s povolenými volbami, např. `"stop": (cp_stop, {"wait"})`.
3. Doplňte řádek do nápovědy `HELP_CPY` / `HELP_MPY` a do návodu `.md`.

Užitečné pomocníky: `say()` a `warn()` pro výpis, `confirm()` pro otázku před nevratnou akcí, `CpyError("...")` pro chybu, kterou uvidí student (bez dlouhého výpisu Pythonu), `Repl` pro sériovou konzoli a `mpremote()` pro MicroPython.

**Podrobný výpis po krocích (`Steps`).** Příkazy, které student spouští z panelu nebo z Run on Save, vypisují očíslované kroky, aby bylo vidět, kde případně nastala chyba. Nový příkaz to dostane takhle:

```python
st = Steps("Nazev akce")                 # nadpis + cas
st.head("Disk desky CIRCUITPY")          # 1) ...
st.info("disk:", drive)                  #    disk:        F:\
st.fail("disk nenalezen.", "rada 1")     # ERROR: v kroku 1 - disk nenalezen. + rady
st.done("Hotovo: ...")                   # zaverecna veta
```

Hotové kroky lze sdílet: `cp_step_drive()` (disk CIRCUITPY), `cp_step_port()` (port CircuitPython desky), `mp_ready_port(opts, st)` (MicroPython deska a její odpověď), `open_repl_step()` a `interrupt_step()` (otevření portu, Ctrl+C), `step_confirm()` (potvrzení / `--yes`) a `step_program_output()` (první výstup programu po restartu).

---

## 10. Simulace a testy na PC (složka `pc/`)

Všechno, co běží jen na počítači, je ve složce **`pc/`** (na desku se nenahrává – v `.ignoreCopy` je `pc/**`):

| Složka | Co obsahuje |
|---|---|
| `pc/_fake` | **falešný hardware** – pro CircuitPython `board`, `digitalio`, `picoed`, `time`, `adafruit_ticks`, `busio`, `pwmio`, `neopixel`, `analogio`; pro MicroPython `machine`, `utime` (jako `time`), `micropython`. Jediný model hardwaru pro testy i simulaci. |
| `pc/_stubs` | typové definice pro nápovědu Pylance (jen pro editor, za běhu se nepoužívají) |
| `pc/tests` | unit testy programu `code.py` (`test_*.py`, `cpy test`) |
| `pc/tests_mpy` | unit testy programu `main.py` (`test_*.py`, `mpy test`) |
| `pc/simulace` | jen pro simulaci: `konzole.py` vypisuje změny hardwaru a čte klávesy; později sem může přibýt „svět“ robota (trať pod senzory čáry) |

### Jeden falešný hardware, dva režimy

Příkazy `cpy sim` / `mpy sim` a `cpy test` / `mpy test` (v `deska.py`, funkce `pc_hardware()`) zaregistrují moduly z `pc/_fake` místo skutečných (`sys.modules["board"] = _fake.board`, …) a přepnou režim v `pc/_fake/_rezim.py`:

| | `cpy test`, `mpy test` (režim `test`) | `cpy sim`, `mpy sim` (režim `sim`) |
|---|---|---|
| Čas | stojí; `time.sleep()` / `adafruit_ticks.advance_ticks()` ho jen posunou, před každým testem se vynuluje | běží podle skutečných hodin; `time.sleep(1)` opravdu čeká |
| Výstup | nic | změny hardwaru vypisuje `pc/simulace/konzole.py` |
| Vstupy | test je nastaví v kódu (`picoed.button_a.set_pressed(True)`, `machine.stiskni("a")`) | klávesy `a` / `b` (tlačítko drží 0,5 s), `q` nebo `Ctrl+C` simulaci ukončí |
| Kontrola | test čte uložený stav (`led.state_history`, `write_history`, `music.history`, …) | člověk čte výpis |

Falešné moduly samy nic nevypisují. Při každé změně jen zavolají `_rezim.oznam(co, kdo, hodnota)` – v testu nikdo neposlouchá, v simulaci posluchač z `konzole.py` změnu vypíše:

```
     test (pc/tests)  ──▶ ┐                             ┌ nic
                          ├─▶ pc/_fake (model) ─ oznam ─┤
     cpy / mpy sim    ──▶ ┘                             └ pc/simulace/konzole.py → výpis
```

Proto platí: **co ukazuje simulace, to ověřují testy** – obojí jde přes stejný kód falešného hardwaru.

### Pořadí a hledání modulů

- CircuitPython (`cpy`): moduly se registrují v pořadí `adafruit_ticks`, `time`, `board`, `digitalio`, `analogio`, `busio`, `pwmio`, `neopixel`, `picoed` (falešný `time` potřebuje `adafruit_ticks`, `picoed` potřebuje `board`, `digitalio` a `busio`).
- MicroPython (`mpy`): `adafruit_ticks`, `utime`, `micropython`, `machine`; `utime` je zároveň `time`. Moduly standardní knihovny s „u“ (`uasyncio`, `ujson`, `ustruct`, …) jsou skutečné moduly Pythonu (`asyncio`, `json`, …).
- Vždy se načte jen jedna sada – `time` má v MicroPythonu jiné funkce (`sleep_ms`, `ticks_ms`) než v CircuitPythonu. Proto má každá platforma svou složku testů.
- Do cesty pro import se přidá kořen projektu (program studenta a jeho moduly), `lib/` (jako `/lib` na desce) a `pc/` (`_fake`, `tests`, `simulace`).
- Testy tak mohou psát `import picoed`, `import _fake.adafruit_ticks as fake_ticks` i `from tests.create import ...` – stejně jako v projektu `3-SW_GIT`, jehož testy projdou přes `cpy test` beze změny (místo jeho `run_test.py`).

### MicroPython: falešný `machine`

- **Deska** (`machine.nastav_desku`): `picoed` (výchozí) nebo `pico` (`mpy sim --pico`). Pico:ed má na sběrnici I2C0 model čipu displeje IS31FL3731 (adresa `0x74`), tlačítka GP20 / GP21 (stisk = 0, jinak pull-up), LED GP25 a bzučák GP3.
- **Pin**: stav pinu je společný pro všechny objekty `Pin(25)` (jako na desce). Změna výstupu se oznámí (`pin`), změna vstupu zavolá obsluhu `irq()` podle `IRQ_RISING` / `IRQ_FALLING`.
- **Timer**: v testu ho spustí posun času – `adafruit_ticks.advance_ticks()` (tedy i `time.sleep_ms`) zavolá `_rezim.casovace(cil_ms)` a ten spustí časovače, které mezitím vyprší, po pořadí. V simulaci čeká na nejbližší časovač vlákno. Tak funguje i odrušení zákmitů v `picoed_v2_lib.Button` (přerušení + jednorázový Timer 20 ms).
- **Displej**: model čipu si pamatuje 8 snímků a ukazuje ten z konfiguračního registru; `obraz()` vrátí 7 × 17 hodnot jasu. Přenos po I2C trvá jako na desce (9 bitů na bajt při `freq`), proto rolování textu trvá stejně dlouho.
- **Knihovna** `lib/picoed_v2_lib` se nemění. `pc/_fake/_mp_knihovny.py` jen obalí `Display.scroll` / `clear` a `Music.play` / `pitch`: oznámí výsledek (text, melodii) a dílčí zápisy uvnitř ztiší (`_rezim.ticho()`), jinak by konzole vypsala každý krok rolování.
- **Klávesy** `a` / `b`: deska zaregistruje, co stisk udělá (`_rezim.registruj_tlacitko`) – falešný `picoed` i falešný `machine`. Konzole volá jen `_rezim.stiskni()`.
- **Reset**: před každým testem `_rezim.resetuj()` vrátí desku do výchozího stavu (piny, časovače, displej).

### Jak dál

- **Scénáře:** sled vstupů v čase („ve 2. s stiskni A, senzor čáry vlevo = 1“) – v simulaci přehrát živě, v testu okamžitě a pak zkontrolovat stav.
- **Svět robota:** poloha JoyCaru a trať v `pc/simulace`, která nastavuje hodnoty falešných senzorů (přes `busio.I2C` a registry expandéru).
- **MicroPython:** NeoPixel, `rp2` (PIO), UART a SPI; BBC micro:bit (modul `microbit`).

---

## 11. Na čem bylo ověřeno

| Co | Verze |
|---|---|
| CircuitPython | 9.2.7 na ELECFREAKS Pico:ed (RP2040), disk `CIRCUITPY` |
| MicroPython | 1.27.0 na Raspberry Pi Pico (RP2040) |
| Systém | Windows 11 (PowerShell, cmd, Git Bash); Ubuntu 24.04 v Dockeru (`setup.sh`, simulace a testy na PC včetně čtení kláves) |
| Knihovny | mpremote 1.27.0, pyserial 3.5, matplotlib 3.11 |

Práce se skutečnou deskou na Linuxu a macOS je napsaná (disky se hledají v `/media/$USER`, `/run/media/$USER`, `/Volumes`), ale na počítači s těmito systémy a připojenou deskou zatím odzkoušená nebyla. macOS nebyl zkoušený vůbec.
