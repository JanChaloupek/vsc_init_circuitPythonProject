# ------------------------------------------------------------
# setup-MicroPython.ps1
#
# Účel:
#   Kompletní instalace a příprava vývojového prostředí
#   pro MicroPython ve VS Code:
#     1) Kontrola Pythonu (případná instalace)
#     2) Kontrola pipu
#     3) Instalace nástroje mpremote
#     4) Detekce VS Code CLI
#     5) Instalace rozšíření MicroPython Panel (.vsix)
#     6) Hromadná instalace doporučených rozšíření z Marketplace
# ------------------------------------------------------------
$ScriptName    = "setup-MicroPython.ps1"
$ScriptVersion = "1.0"
$ScriptDate    = "2026-11-23"

. "$PSScriptRoot/utils.ps1"

Write-Host "============================================================" @ColorInfo
Write-Host "  $ScriptName - verze: $ScriptVersion ($ScriptDate)" @ColorInfo
Write-Host "  Priprava prostredi pro MicroPython" @ColorInfo
Write-Host "============================================================"
Write-Host ""

# ------------------------------------------------------------
# 1) Check Python
# ------------------------------------------------------------
Write-Host "[1/6] Kontrola Pythonu..." @ColorInfo

python --version 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Python nenalezen. Stahuji instalator..." @ColorError

    $installer = "$env:TEMP\python-installer.exe"
    Invoke-WebRequest -Uri "https://www.python.org/ftp/python/3.12.2/python-3.12.2-amd64.exe" -OutFile $installer

    Write-Host "Instaluji Python..." @ColorInfo
    Start-Process -FilePath $installer -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1" -Wait

    Write-Host "Python nainstalovan." @ColorDone
} else {
    Write-Host "Python OK" @ColorDone
}
Write-Host "--------------------------------------"

# ------------------------------------------------------------
# 2) Check pip
# ------------------------------------------------------------
Write-Host "[2/6] Kontrola pipu..." @ColorInfo

python -m pip --version 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "pip nenalezen. Instaluji..." @ColorError

    python -m ensurepip --default-pip
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Instalace pipu selhala." @ColorError
        exit 1
    }

    Write-Host "pip nainstalovan." @ColorDone
} else {
    Write-Host "pip OK" @ColorDone
}
Write-Host "--------------------------------------"

# ------------------------------------------------------------
# 3) Check mpremote
# ------------------------------------------------------------
Write-Host "[3/6] Kontrola mpremote..." @ColorInfo

python -m mpremote --help >$null 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "mpremote nenalezen. Instaluji..." @ColorInfo

    python -m pip install mpremote
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Instalace mpremote selhala." @ColorError
        exit 1
    }

    Write-Host "mpremote nainstalovan." @ColorDone
} else {
    Write-Host "mpremote OK" @ColorDone
}
Write-Host "--------------------------------------"

# ------------------------------------------------------------
# 4) Detekce VS Code CLI
# ------------------------------------------------------------
Write-Host "[4/6] Detekce VS Code CLI..." @ColorInfo

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
    Write-Host "VS Code CLI nenalezen. Preskakuji instalaci rozsireni." @ColorError
    exit 1
} else {
    Write-Host "VS Code CLI nalezen: $codeCmd" @ColorDone
}
Write-Host "--------------------------------------"

# ------------------------------------------------------------
# 5) Instalace MicroPython Panelu
# ------------------------------------------------------------
Write-Host "[5/6] Instalace MicroPython Panelu..." @ColorInfo

$vsix = Join-Path $PSScriptRoot "dist\micropython-panel.vsix"
if (Test-Path $vsix) {
    & $codeCmd --install-extension $vsix --force
    if ($LASTEXITCODE -eq 0) {
        Write-Host "MicroPython Panel uspesne nainstalovan/aktualizovan." @ColorDone
    } else {
        Write-Host "Instalace MicroPython Panelu selhala." @ColorError
    }
} else {
    Write-Host "Balicek $vsix nebyl nalezen." @ColorError
}
Write-Host "--------------------------------------"

# ------------------------------------------------------------
# 6) Hromadne instalace rozsireni z Marketplace
# ------------------------------------------------------------
Write-Host "[6/6] Instalace doporucenych rozsireni z Marketplace..." @ColorInfo

$microExtensions = @(
    "ms-python.python",
    "ms-python.vscode-pylance",
    "streetsidesoftware.code-spell-checker",
    "streetsidesoftware.code-spell-checker-czech",
    "oderwat.indent-rainbow",
    "ms-vscode.powershell"
)

foreach ($extId in $microExtensions) {
    Write-Host "  -> Instaluji $extId ... " -NoNewline
    & $codeCmd --install-extension $extId --force | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK]" @ColorDone
    } else {
        Write-Host "[CHYBA]" @ColorError
    }
}

Write-Host "--------------------------------------"
Write-Host "Instalace prostredi MicroPython je KOMPLETNI!" @ColorDone
Write-Host "Nyni muzete otevrit projekt ve VS Code." @ColorInfo
