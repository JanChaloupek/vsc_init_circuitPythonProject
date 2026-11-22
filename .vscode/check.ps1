# ------------------------------------------------------------
# Diagnostika MicroPython zařízení
#
# Ucel:
#   Provede diagnostiku MicroPython zarizeni:
#     - Najde spravny COM port
#     - Otestuje REPL (zda zarizeni reaguje)
#     - Zobrazi informace o filesystemu
#     - Vypise obsah zarizeni (stromove)
#
# Pouziti:
#   powershell -ExecutionPolicy Bypass -File ./.vscode/check.ps1
#
# Vyuziva utils.ps1, list_tmp.py (docasny soubor)
# ------------------------------------------------------------
$ScriptName    = "check.ps1"
$ScriptVersion = "1.2"
$ScriptDate    = "2026-01-26"

. "$PSScriptRoot/utils.ps1"

Write-Host "$ScriptName - verze: $ScriptVersion ($ScriptDate)" @ColorInfo
Write-Host "======================================"

# ------------------------------------------------------------
# 1) Detekce portu
# ------------------------------------------------------------
$port = Get-ReadyPort
Write-Host "Pouzivam port: " -NoNewline
Write-Host $port @ColorInfo
Write-Host "--------------------------------------"

# ------------------------------------------------------------
# 2) Test REPL
# ------------------------------------------------------------
Write-Host "Testuji REPL..." @ColorInfo
python -m mpremote connect $port exec "pass" 2>$null

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR" @ColorError -NoNewline
    Write-Host ": Zarizeni nereaguje."
    exit 1
}

Write-Host "REPL OK" @ColorDone
Write-Host "--------------------------------------"

# ------------------------------------------------------------
# 3) Informace o filesystemu
# ------------------------------------------------------------
Write-Host "Informace o filesystemu:" @ColorInfo

$tmpInfo = "$PSScriptRoot/check_info_tmp.py"

@"
import os
s = os.statvfs("/")
total = s[0] * s[2]
free  = s[0] * s[3]
print("Total:", total, "B")
print("Free :", free,  "B")
"@ | Out-File -Encoding ascii $tmpInfo

python -m mpremote connect $port run $tmpInfo
Remove-Item $tmpInfo -Force

Write-Host "--------------------------------------"

# ------------------------------------------------------------
# 4) Stromovy vypis obsahu
# ------------------------------------------------------------
Write-Host "Obsah zarizeni:" @ColorInfo
powershell -ExecutionPolicy Bypass -File "$PSScriptRoot/list.ps1"

Write-Host "======================================"
Write-Host "Diagnostika dokoncena." @ColorDone
