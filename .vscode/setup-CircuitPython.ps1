# ------------------------------------------------------------
# setup-CircuitPython.ps1
#
# Účel:
#   Kompletní instalace a příprava vývojového prostředí
#   pro CircuitPython ve VS Code:
#     1) Kontrola Pythonu (případná instalace)
#     2) Kontrola pipu
#     3) Detekce VS Code CLI
#     4) Hromadná instalace rozšíření pro CircuitPython z Marketplace
#     5) Kontrola připojeného USB disku CIRCUITPY
# ------------------------------------------------------------
$ScriptName    = "setup-CircuitPython.ps1"
$ScriptVersion = "1.0"
$ScriptDate    = "2026-11-23"

. "$PSScriptRoot/utils.ps1"

Write-Host "============================================================" @ColorInfo
Write-Host "  $ScriptName - verze: $ScriptVersion ($ScriptDate)" @ColorInfo
Write-Host "  Priprava prostredi pro CircuitPython" @ColorInfo
Write-Host "============================================================"
Write-Host ""

# ------------------------------------------------------------
# 1) Check Python
# ------------------------------------------------------------
Write-Host "[1/5] Kontrola Pythonu..." @ColorInfo

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
Write-Host "[2/5] Kontrola pipu..." @ColorInfo

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
# 3) Detekce VS Code CLI
# ------------------------------------------------------------
Write-Host "[3/5] Detekce VS Code CLI..." @ColorInfo

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
# 4) Hromadná instalace rozšíření pro CircuitPython
# ------------------------------------------------------------
Write-Host "[4/5] Instalace CircuitPython rozsireni z Marketplace..." @ColorInfo

$circuitExtensions = @(
    "ms-python.python",
    "ms-python.vscode-pylance",
    "wmerkens.vscode-circuitpython-v2-cursor-ai",
    "streetsidesoftware.code-spell-checker",
    "streetsidesoftware.code-spell-checker-czech",
    "oderwat.indent-rainbow",
    "ms-vscode.powershell"
)

foreach ($extId in $circuitExtensions) {
    Write-Host "  -> Instaluji $extId ... " -NoNewline
    & $codeCmd --install-extension $extId --force | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK]" @ColorDone
    } else {
        Write-Host "[CHYBA]" @ColorError
    }
}
Write-Host "--------------------------------------"

# ------------------------------------------------------------
# 5) Detekce USB disku CIRCUITPY
# ------------------------------------------------------------
Write-Host "[5/5] Kontrola pripojeni zarizeni CircuitPython..." @ColorInfo

$circuitDrive = Get-Volume | Where-Object { $_.FileSystemLabel -like "*CIRCUIT*" } | Select-Object -First 1

if ($circuitDrive) {
    Write-Host "Nalezen disk CircuitPython: $($circuitDrive.DriveLetter): ($($circuitDrive.FileSystemLabel))" @ColorDone
    
    $bootOut = "$($circuitDrive.DriveLetter):\boot_out.txt"
    if (Test-Path $bootOut) {
        $info = Get-Content $bootOut -TotalCount 1
        Write-Host "  Verze na desce: $info" @ColorInfo
    }
} else {
    Write-Host "Upozorneni: Zadny disk CIRCUITPY neni prave pripojen." @ColorFile
    Write-Host "  (Po pripojeni desky do USB se zobrazi jako flash disk.)"
}

Write-Host "--------------------------------------"
Write-Host "Instalace prostredi CircuitPython je KOMPLETNI!" @ColorDone
Write-Host "Nyni muzete otevrit projekt ve VS Code." @ColorInfo
