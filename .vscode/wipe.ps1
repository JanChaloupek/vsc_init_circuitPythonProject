# ------------------------------------------------------------
# Smaže všechny soubory a adresáře z MicroPython zařízení
#
# Použití:
#   powershell -ExecutionPolicy Bypass -File wipe.ps1
#
# Popis:
#   Tento skript kompletně vymaže obsah souborového systému
#   MicroPython zařízení (všechny soubory i adresáře).
#
# Vlastnosti:
#   - Rekurzivní mazání celého obsahu zařízení
#   - Automatická detekce správného COM portu
#   - Automatický reset zařízení, pokud nereaguje
#   - Bezpečné spuštění přes dočasný MicroPython skript
#
# Typické použití:
#   - příprava zařízení pro nový projekt
#   - vyčištění zařízení před výukou
#   - odstranění starých nebo zapomenutých souborů
#
# Upozornění:
#   - Operace je NEVRATNÁ
#   - Všechna data v zařízení budou smazána
#   - Skript nemaže nic na počítači, pouze v zařízení
#
# Poznámky:
#   - Skript automaticky detekuje správný COM port
#   - Pokud zařízení nereaguje, provede se automatický reset
#   - Výpis chyb při mazání je informativní (např. zamčené soubory)
#
# Vyžaduje:
#   - utils.ps1 ve stejné složce
#   - funkční mpremote a Python v PATH
# ------------------------------------------------------------
$ScriptName    = "wipe.ps1"
$ScriptVersion = "3.4"
$ScriptDate    = "2026-01-26"

. "$PSScriptRoot/utils.ps1"

Write-Host "$ScriptName - verze: $ScriptVersion ($ScriptDate)" @ColorInfo
Write-Host "--------------------------------------"

$port = Get-ReadyPort
Write-Host "Pouzivam port: " -NoNewline
Write-Host $port @ColorInfo

Write-Host "Mazani zarizeni..."
Write-Host "--------------------------------------"

$tmp = "$PSScriptRoot/wipe_tmp.py"

@'
import os

def wipe(path=''):
    for name in os.listdir(path):
        full = name if path == '' else path + '/' + name
        try:
            st = os.stat(full)[0]
            if st & 0x4000:  # directory
                wipe(full)
                os.rmdir(full)
            else:
                os.remove(full)
        except Exception as e:
            print("ERR:", full, e)

wipe()
'@ | Out-File -Encoding ascii $tmp   # ASCII = bez BOM (nutné pro MicroPython)

Write-Host "Spoustim mazani..." @ColorInfo
Set-Location $PSScriptRoot
python -m mpremote connect $port run wipe_tmp.py

Remove-Item $tmp -Force

Write-Host "--------------------------------------"
Write-Host "Wipe complete." @ColorDone
Write-Host "--------------------------------------"