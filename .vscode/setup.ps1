# ------------------------------------------------------------
# setup.ps1
#
# Účel:
#   Kompletní jednorázová příprava vývojového prostředí
#   pro MicroPython i CircuitPython ve VS Code:
#     1) Kontrola Pythonu (případná tichá instalace)
#     2) Kontrola pipu
#     3) Instalace nástroje mpremote (pro MicroPython)
#     4) Detekce VS Code CLI
#     5) Instalace rozšíření MicroPython Panel (.vsix)
#     6) Hromadná instalace rozšíření z Marketplace (obě platformy)
#     7) Kontrola a detekce připojeného hardware (Pico, Pico:ed apod.)
# ------------------------------------------------------------
$ScriptName    = "setup.ps1"
$ScriptVersion = "2.0"
$ScriptDate    = "2026-11-24"

. "$PSScriptRoot/utils.ps1"

Write-Host "============================================================" @ColorInfo
Write-Host "  $ScriptName - verze: $ScriptVersion ($ScriptDate)" @ColorInfo
Write-Host "  Kompletni priprava prostredi: MicroPython & CircuitPython" @ColorInfo
Write-Host "============================================================"
Write-Host ""

# ------------------------------------------------------------
# 1) Check Python
# ------------------------------------------------------------
Write-Host "[1/7] Kontrola instalace Pythonu..." @ColorInfo

python --version 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Python nenalezen. Stahuji instalator z python.org..." @ColorError

    $installer = "$env:TEMP\python-installer.exe"
    Invoke-WebRequest -Uri "https://www.python.org/ftp/python/3.12.2/python-3.12.2-amd64.exe" -OutFile $installer

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
Write-Host "[2/7] Kontrola balickovaciho nastroje pip..." @ColorInfo

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
Write-Host "[3/7] Kontrola nastroje mpremote (MicroPython)..." @ColorInfo

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
Write-Host "--------------------------------------"

# ------------------------------------------------------------
# 4) Detekce VS Code CLI
# ------------------------------------------------------------
Write-Host "[4/7] Detekce rozhrani VS Code CLI..." @ColorInfo

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
# 5) Instalace MicroPython Panelu
# ------------------------------------------------------------
Write-Host "[5/7] Instalace rozsireni MicroPython Panel..." @ColorInfo

$vsix = Join-Path $PSScriptRoot "dist\micropython-panel.vsix"
if (Test-Path $vsix) {
    & $codeCmd --install-extension $vsix --force
    if ($LASTEXITCODE -eq 0) {
        Write-Host "MicroPython Panel uspesne nainstalovan/aktualizovan." @ColorDone
    } else {
        Write-Host "Instalace MicroPython Panelu selhala." @ColorError
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
# 7) Kontrola a nastaveni automatickeho nahravani (Run on Save)
# ------------------------------------------------------------
Write-Host "[7/8] Kontrola automatickeho nahravani (Run on Save)..." @ColorInfo

$settingsFile = Join-Path $PSScriptRoot "settings.json"
if (Test-Path $settingsFile) {
    $rawSettings = Get-Content $settingsFile -Raw
    if ($rawSettings -match "emeraldwalk\.runonsave") {
        Write-Host "  -> Run on Save je spravne nakonfigurovan v settings.json." @ColorDone
    } else {
        Write-Host "  -> Doplnuji konfiguraci Run on Save pro Windows..." @ColorInfo
        try {
            $jsonObj = $rawSettings | ConvertFrom-Json
            $runOnSaveCmd = @{
                commands = @(
                    @{
                        match   = ".*\.py"
                        isAsync = $true
                        cmd     = "powershell -ExecutionPolicy Bypass -NoProfile -File `"`${workspaceFolder}\.vscode\copy.ps1`" `"`${workspaceFolder}`" `"`${relativeFile}`" `".vscode\.ignoreCopy`""
                    }
                )
            }
            $jsonObj | Add-Member -NotePropertyName "emeraldwalk.runonsave" -NotePropertyValue $runOnSaveCmd -Force
            $jsonObj | ConvertTo-Json -Depth 10 | Set-Content $settingsFile -Encoding UTF8
            Write-Host "  -> Konfigurace Run on Save byla uspesne zapsana." @ColorDone
        } catch {
            Write-Host "  -> Upozorneni: Nepodarilo se automaticky zapsat do settings.json ($($_.Exception.Message))" @ColorError
        }
    }
}
Write-Host "--------------------------------------"

# ------------------------------------------------------------
# 8) Detekce pripojeneho hardware
# ------------------------------------------------------------
Write-Host "[8/8] Kontrola pripojeni vyvojove desky..." @ColorInfo

$hwFound = $false

# A) CircuitPython disk
$circuitDrive = Get-Volume 2>$null | Where-Object { $_.FileSystemLabel -like "*CIRCUIT*" } | Select-Object -First 1
if ($circuitDrive) {
    Write-Host "  [CircuitPython] Nalezen disk: $($circuitDrive.DriveLetter): ($($circuitDrive.FileSystemLabel))" @ColorDone
    $bootOut = "$($circuitDrive.DriveLetter):\boot_out.txt"
    if (Test-Path $bootOut) {
        $info = Get-Content $bootOut -TotalCount 1
        Write-Host "    -> $info" @ColorInfo
    }
    $hwFound = $true
}

# B) MicroPython desky pres mpremote
$devs = python -m mpremote devs 2>$null
if ($devs) {
    $lines = $devs -split "`r?`n" | Where-Object { $_.Trim() -ne "" }
    foreach ($line in $lines) {
        Write-Host "  [MicroPython] Nalezen COM port: $line" @ColorDone
        $hwFound = $true
    }
}

if (-not $hwFound) {
    Write-Host "  Zadna deska neni prave pripojena pres USB (to nevadi, prostredi je pripraveno)." @ColorFile
}

Write-Host "============================================================" @ColorDone
Write-Host "  Instalace je KOMPLETNI! Prostredi je pripraveno." @ColorDone
Write-Host "  Muzete pracovat s MicroPythonem i CircuitPythonem." @ColorDone
Write-Host "============================================================" @ColorDone
