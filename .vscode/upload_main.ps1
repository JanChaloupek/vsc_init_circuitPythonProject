# ------------------------------------------------------------
# Nahraje pouze main.py na MicroPython zařízení
#
# Účel:
#   Tento skript rychle nahraje nebo aktualizuje soubor main.py
#   na MicroPython zařízení bez nahrávání celého projektu.
#
# Použití:
#   powershell -ExecutionPolicy Bypass -File ./.vscode/upload_main.ps1
#
# Typické použití:
#   - rychlé ladění
#   - aktualizace hlavního programu
#   - výuka, kde studenti často mění jen main.py
#
# Vyžaduje:
#   - utils.ps1 ve stejné složce
#   - funkční mpremote a Python v PATH
# ------------------------------------------------------------
$ScriptName    = "upload_main.ps1"
$ScriptVersion = "1.0"
$ScriptDate    = "2026-01-27"

. "$PSScriptRoot/utils.ps1"

Write-Host "$ScriptName - verze: $ScriptVersion ($ScriptDate)" @ColorInfo
Write-Host "--------------------------------------"

# ------------------------------------------------------------
# 1) Kontrola existence main.py
# ------------------------------------------------------------
$main = "main.py"

if (-not (Test-Path $main)) {
    Write-Host "ERROR" @ColorError -NoNewline
    Write-Host ": Soubor main.py nebyl nalezen v aktualni slozce."
    exit 1
}

Write-Host "Nahravam soubor: " -NoNewline
Write-Host $main @ColorFile

# ------------------------------------------------------------
# 2) Detekce portu
# ------------------------------------------------------------
$port = Get-ReadyPort
Write-Host "Pouzivam port: " -NoNewline
Write-Host $port @ColorInfo
Write-Host "--------------------------------------"

# ------------------------------------------------------------
# 3) Nahrání main.py
# ------------------------------------------------------------
python -m mpremote connect $port cp $main ":"

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR" @ColorError -NoNewline
    Write-Host ": Nahrani selhalo."
    exit 1
}

Write-Host "--------------------------------------"
Write-Host "main.py uspesne nahran." @ColorDone
Write-Host "--------------------------------------"
