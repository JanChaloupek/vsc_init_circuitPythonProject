# ------------------------------------------------------------
# MicroPython REPL
#
# Účel:
#   Spustí interaktivní MicroPython REPL na detekovaném zařízení.
#
# Použití:
#   powershell -ExecutionPolicy Bypass -File ./.vscode/repl.ps1
#
# Popis:
#   - Automaticky detekuje správný COM port
#   - Spustí REPL přes mpremote
#   - Barevné hlášky před i po ukončení REPL
#
# Vyžaduje:
#   - utils.ps1 ve stejné složce
#   - funkční mpremote a Python v PATH
# ------------------------------------------------------------
$ScriptName    = "repl.ps1"
$ScriptVersion = "1.0"
$ScriptDate    = "2026-01-27"

. "$PSScriptRoot/utils.ps1"

Write-Host "$ScriptName - verze: $ScriptVersion ($ScriptDate)" @ColorInfo
Write-Host "--------------------------------------"

# ------------------------------------------------------------
# 1) Detekce portu
# ------------------------------------------------------------
$port = Get-ReadyPort
Write-Host "Pouzivam port: " -NoNewline
Write-Host $port @ColorInfo
Write-Host "--------------------------------------"

# ------------------------------------------------------------
# 2) Spuštění REPL
# ------------------------------------------------------------
Write-Host "Spouštím MicroPython REPL..." @ColorInfo
Write-Host "Ukončení: CTRL+]" @ColorInfo
Write-Host "--------------------------------------"

python -m mpremote connect $port repl

# ------------------------------------------------------------
# 3) Výsledek po ukončení REPL
# ------------------------------------------------------------
Write-Host "--------------------------------------"

if ($LASTEXITCODE -eq 0) {
    Write-Host "REPL ukončen úspěšně." @ColorDone
} else {
    Write-Host "ERROR" @ColorError -NoNewline
    Write-Host ": REPL skončil s chybou."
}

Write-Host "--------------------------------------"
