# ------------------------------------------------------------
# Kontrola instalace Pythonu, pipu a mpremote
#
# Ucel:
#   Zkontroluje instalaci Pythonu, pipu a mpremote.
#   Pokud neco chybi, pokusi se to nainstalovat.
#   Spousti se pouze jednou po instalaci VS Code.
# ------------------------------------------------------------
$ScriptName    = "setup.ps1"
$ScriptVersion = "1.1"
$ScriptDate    = "2026-01-26"

. "$PSScriptRoot/utils.ps1"

Write-Host "$ScriptName - version: $ScriptVersion ($ScriptDate)" @ColorInfo
Write-Host "--------------------------------------"

# ------------------------------------------------------------
# 1) Check Python
# ------------------------------------------------------------
Write-Host "Checking Python..." @ColorInfo

python --version 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Python not found." @ColorError
    Write-Host "Downloading Python installer..." @ColorInfo

    $installer = "$env:TEMP\python-installer.exe"
    Invoke-WebRequest -Uri "https://www.python.org/ftp/python/3.12.2/python-3.12.2-amd64.exe" -OutFile $installer

    Write-Host "Installing Python..." @ColorInfo
    Start-Process -FilePath $installer -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1" -Wait

    Write-Host "Python installed." @ColorDone
} else {
    Write-Host "Python OK" @ColorDone
}

Write-Host "--------------------------------------"

# ------------------------------------------------------------
# 2) Check pip
# ------------------------------------------------------------
Write-Host "Checking pip..." @ColorInfo

python -m pip --version 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "pip not found. Installing..." @ColorError

    python -m ensurepip --default-pip
    if ($LASTEXITCODE -ne 0) {
        Write-Host "pip installation failed." @ColorError
        exit 1
    }

    Write-Host "pip installed." @ColorDone
} else {
    Write-Host "pip OK" @ColorDone
}

Write-Host "--------------------------------------"

# ------------------------------------------------------------
# 3) Check mpremote
# ------------------------------------------------------------
Write-Host "Checking mpremote..." @ColorInfo

python -m mpremote --help >$null 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "mpremote not found. Installing..." @ColorError

    python -m pip install mpremote
    if ($LASTEXITCODE -ne 0) {
        Write-Host "mpremote installation failed." @ColorError
        exit 1
    }

    Write-Host "mpremote installed." @ColorDone
} else {
    Write-Host "mpremote OK" @ColorDone
}

Write-Host "--------------------------------------"

# ------------------------------------------------------------
# 4) Instaling MicroPython-panel
# ------------------------------------------------------------
Write-Host "Installing MicroPython VS Code extension..." @ColorInfo

$vsix = Join-Path $PSScriptRoot "dist/micropython-panel.vsix"

# Robustní autodetekce VS Code CLI
Write-Host "Checking for VS Code CLI..."

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

# 1) Zkus PATH
if (Get-Command "code" -ErrorAction SilentlyContinue) {
    $codeCmd = "code"
}

# 2) Pokud není v PATH, hledej v typických instalacích
if (-not $codeCmd) {
    foreach ($path in $possiblePaths) {
        if (Test-Path $path) {
            $codeCmd = $path
            break
        }
    }
}

# 3) Vyhodnocení výsledku
if (-not $codeCmd) {
    Write-Host "VS Code CLI not found. Skipping extension installation." @ColorError
} else {
    Write-Host "VS Code CLI found at: $codeCmd" @ColorDone
    & $codeCmd --install-extension $vsix --force
    if ($LASTEXITCODE -eq 0) {
        Write-Host "MicroPython extension installed/updated." @ColorDone
    } else {
        Write-Host "Extension installation failed." @ColorError
    }
}

Write-Host "--------------------------------------"
Write-Host "Setup complete. You can continue." @ColorDone
