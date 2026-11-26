# ------------------------------------------------------------
# setup.ps1
#
# Ucel:
#   Kompletni jednorazova priprava vyvojoveho prostredi
#   pro MicroPython i CircuitPython ve VS Code:
#     1) Kontrola Pythonu (pripadna ticha instalace)
#     2) Kontrola balickovaciho nastroje pip
#     3) Instalace Python knihoven: mpremote (MicroPython, obsahuje
#        i pyserial) a matplotlib (graf hodnot: mpy plot / cpy plot)
#     4) Detekce VS Code CLI
#     5) Instalace rozsireni MicroPython & CircuitPython Panel (.vsix)
#     6) Hromadna instalace rozsireni z Marketplace (obe platformy)
#     7) Nastaveni panelu a Run on Save v settings.json
#        (zapisuje je .vscode/deska.py vscode - tlacitka jsou
#        definovana jen tam, stejne pro Windows i Linux/macOS)
#     8) Kontrola pripojenych desek (.vscode/deska.py devices)
#
# Vsechny ostatni nastroje (mpy, cpy) jsou v jedinem souboru
# .vscode/deska.py. Tento skript zustava v PowerShellu, protoze
# musi umet nainstalovat i samotny Python.
# ------------------------------------------------------------
$ScriptName    = "setup.ps1"
$ScriptVersion = "3.0"
$ScriptDate    = "2026-11-26"

# Barevne profily vypisu (drive v utils.ps1)
$ColorInfo  = @{ ForegroundColor = "Cyan" }
$ColorError = @{ ForegroundColor = "Red" }
$ColorFile  = @{ ForegroundColor = "Yellow" }
$ColorDone  = @{ ForegroundColor = "Green" }

$DeskaPy = Join-Path $PSScriptRoot "deska.py"

Write-Host "============================================================" @ColorInfo
Write-Host "  $ScriptName - verze: $ScriptVersion ($ScriptDate)" @ColorInfo
Write-Host "  Kompletni priprava prostredi: MicroPython & CircuitPython" @ColorInfo
Write-Host "============================================================"
Write-Host ""

# ------------------------------------------------------------
# 1) Check Python
# ------------------------------------------------------------
Write-Host "[1/8] Kontrola instalace Pythonu..." @ColorInfo

python --version 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Python nenalezen. Stahuji instalator z python.org..." @ColorError

    $installer = "$env:TEMP\python-installer.exe"
    Invoke-WebRequest -Uri "https://www.python.org/ftp/python/3.12.8/python-3.12.8-amd64.exe" -OutFile $installer

    Write-Host "Instaluji Python..." @ColorInfo
    Start-Process -FilePath $installer -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1" -Wait

    Write-Host "Python uspesne nainstalovan." @ColorDone
} else {
    $pyVer = python --version 2>&1
    Write-Host "Python OK ($pyVer)" @ColorDone
}
Write-Host "--------------------------------------"

# ------------------------------------------------------------
# 2) Check pip
# ------------------------------------------------------------
Write-Host "[2/8] Kontrola balickovaciho nastroje pip..." @ColorInfo

python -m pip --version 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "pip nenalezen. Inicializuji..." @ColorError

    python -m ensurepip --default-pip
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Instalace pipu selhala." @ColorError
        exit 1
    }

    Write-Host "pip uspesne nainstalovan." @ColorDone
} else {
    Write-Host "pip OK" @ColorDone
}
Write-Host "--------------------------------------"

# ------------------------------------------------------------
# 3) Check mpremote (MicroPython komunikace)
# ------------------------------------------------------------
Write-Host "[3/8] Kontrola Python knihoven (mpremote, matplotlib)..." @ColorInfo

python -m mpremote --help >$null 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "mpremote nenalezen. Instaluji pres pip..." @ColorInfo

    python -m pip install mpremote
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Instalace mpremote selhala." @ColorError
        exit 1
    }

    Write-Host "mpremote uspesne nainstalovan." @ColorDone
} else {
    Write-Host "mpremote OK" @ColorDone
}

# matplotlib je potreba jen pro graf (mpy plot / cpy plot)
python -c "import matplotlib" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "matplotlib (graf) nenalezen. Instaluji pres pip..." @ColorInfo
    python -m pip install matplotlib
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Instalace matplotlib selhala (graf nebude fungovat, ostatni ano)." @ColorError
    } else {
        Write-Host "matplotlib uspesne nainstalovan." @ColorDone
    }
} else {
    Write-Host "matplotlib OK" @ColorDone
}
Write-Host "--------------------------------------"

# ------------------------------------------------------------
# 4) Detekce VS Code CLI
# ------------------------------------------------------------
Write-Host "[4/8] Detekce rozhrani VS Code CLI..." @ColorInfo

$possiblePaths = @(
    "$env:LOCALAPPDATA\Programs\Microsoft VS Code\bin\code.cmd",
    "$env:LOCALAPPDATA\Programs\Microsoft VS Code Insiders\bin\code-insiders.cmd",
    "C:\Program Files\Microsoft VS Code\bin\code.cmd",
    "C:\Program Files\Microsoft VS Code\bin\code-insiders.cmd",
    "C:\Program Files\Microsoft VS Code\bin\code-arm64.cmd",
    "C:\Program Files (x86)\Microsoft VS Code\bin\code.cmd",
    "C:\Program Files (x86)\Microsoft VS Code\bin\code-insiders.cmd"
)

$codeCmd = $null
if (Get-Command "code" -ErrorAction SilentlyContinue) {
    $codeCmd = "code"
}

if (-not $codeCmd) {
    foreach ($path in $possiblePaths) {
        if (Test-Path $path) {
            $codeCmd = $path
            break
        }
    }
}

if (-not $codeCmd) {
    Write-Host "VS Code CLI nenalezen. Preskakuji automatickou instalaci rozsireni." @ColorError
    exit 1
} else {
    Write-Host "VS Code CLI nalezen: $codeCmd" @ColorDone
}
Write-Host "--------------------------------------"

# ------------------------------------------------------------
# 5) Instalace MicroPython & CircuitPython Panelu
# ------------------------------------------------------------
Write-Host "[5/8] Instalace rozsireni MicroPython & CircuitPython Panel..." @ColorInfo

$vsix = Join-Path $PSScriptRoot "dist\micropython-panel.vsix"
if (Test-Path $vsix) {
    & $codeCmd --install-extension $vsix --force
    if ($LASTEXITCODE -eq 0) {
        Write-Host "MicroPython & CircuitPython Panel uspesne nainstalovan/aktualizovan." @ColorDone
    } else {
        Write-Host "Instalace panelu selhala." @ColorError
    }
} else {
    Write-Host "Upozorneni: Balicek $vsix nebyl nalezen." @ColorError
}
Write-Host "--------------------------------------"

# ------------------------------------------------------------
# 6) Hromadne instalace rozsireni z Marketplace
# ------------------------------------------------------------
Write-Host "[6/8] Instalace spolecnych rozsireni z Marketplace..." @ColorInfo

$allExtensions = @(
    @{ Id = "ms-python.python";                            Name = "Python (jazykova podpora)" },
    @{ Id = "ms-python.vscode-pylance";                   Name = "Pylance (analyza kodu a naseptavani)" },
    @{ Id = "wmerkens.vscode-circuitpython-v2-cursor-ai";  Name = "CircuitPython podpora (0.3.3)" },
    @{ Id = "emeraldwalk.runonsave";                       Name = "Run on Save (automaticke nahravani)" },
    @{ Id = "streetsidesoftware.code-spell-checker";       Name = "Code Spell Checker" },
    @{ Id = "streetsidesoftware.code-spell-checker-czech"; Name = "Czech - Code Spell Checker" },
    @{ Id = "oderwat.indent-rainbow";                      Name = "Indent Rainbow (barevne odsazeni)" },
    @{ Id = "ms-vscode.powershell";                        Name = "PowerShell podpora" },
    @{ Id = "jebbs.plantuml";                              Name = "PlantUML (diagramy trid robota)" },
    @{ Id = "IBM.output-colorizer";                        Name = "Output Colorizer (barevne logy)" },
    @{ Id = "eugenejeon.codesnap-plus-fix";                Name = "CodeSnap-plus-fix (snimky kodu pro PR)" }
)

foreach ($ext in $allExtensions) {
    Write-Host "  -> Instaluji $($ext.Name) ... " -NoNewline
    & $codeCmd --install-extension $ext.Id --force | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK]" @ColorDone
    } else {
        Write-Host "[CHYBA]" @ColorError
    }
}
Write-Host "--------------------------------------"

# ------------------------------------------------------------
# 7) Kontrola a nastaveni settings.json pro Windows
# ------------------------------------------------------------
Write-Host "[7/8] Nastaveni panelu a Run on Save (settings.json)..." @ColorInfo

# Tlacitka panelu i Run on Save jsou definovana v deska.py (PANEL_BUTTONS),
# aby byla stejna pro Windows i Linux/macOS.
python $DeskaPy vscode
if ($LASTEXITCODE -ne 0) {
    Write-Host "  -> Upozorneni: settings.json se nepodarilo nastavit." @ColorError
}
Write-Host "--------------------------------------"

# ------------------------------------------------------------
# 8) Detekce pripojeneho hardware
# ------------------------------------------------------------
Write-Host "[8/8] Kontrola pripojenych desek..." @ColorInfo

# Vypise desky s CircuitPythonem (disk CIRCUITPY) i MicroPythonem (COM port).
# Kdyz neni pripojena zadna deska, nevadi to - prostredi je pripraveno.
python $DeskaPy devices

Write-Host "============================================================" @ColorDone
Write-Host "  Instalace je KOMPLETNI! Prostredi je pripraveno." @ColorDone
Write-Host "  Muzete pracovat s MicroPythonem i CircuitPythonem." @ColorDone
Write-Host "============================================================" @ColorDone
