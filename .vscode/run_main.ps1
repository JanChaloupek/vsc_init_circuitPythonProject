# ------------------------------------------------------------
# Spustí main.py na MicroPython zařízení (bez nahrávání)
#
# Účel:
#   Tento skript spustí main.py přímo na zařízení pomocí mpremote.
#   Soubor main.py musí být již nahrán v zařízení.
#
# Použití:
#   powershell -ExecutionPolicy Bypass -File ./.vscode/run_main.ps1
#
# Typické použití:
#   - rychlé testování programu
#   - výuka, kde studenti často mění main.py
#
# Vyžaduje:
#   - utils.ps1 ve stejné složce
#   - funkční mpremote a Python v PATH
# ------------------------------------------------------------
$ScriptName    = "run_main.ps1"
$ScriptVersion = "1.0"
$ScriptDate    = "2026-01-27"

. "$PSScriptRoot/utils.ps1"

Write-Host "$ScriptName - verze: $ScriptVersion ($ScriptDate)" @ColorInfo
Write-Host "--------------------------------------"

# 1) Detekce portu
$port = Get-ReadyPort
Write-Host "Používám port: " -NoNewline
Write-Host $port @ColorInfo
Write-Host "--------------------------------------"

# 2) Spuštění main.py
Write-Host "Spouštím main.py..." @ColorInfo
python -m mpremote connect $port run main.py

Write-Host "--------------------------------------"

if ($LASTEXITCODE -eq 0) {
    Write-Host "main.py dokončen." @ColorDone
} else {
    Write-Host "ERROR" @ColorError -NoNewline
    Write-Host ": Spuštění selhalo."
}

Write-Host "--------------------------------------"
