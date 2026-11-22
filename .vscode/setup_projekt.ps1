# ------------------------------------------------------------
# Kompletní priprava MicroPython zarizeni
#
# Ucel:
#   Tento skript provede kompletní pripravu MicroPython zarizeni
#   pro aktualni projekt:
#
#       1) Smaze vsechny soubory (wipe)
#       2) Nahraje projekt podle upload_config.txt (upload)
#       3) Vypise obsah zarizeni (list)
#
#   Skript je urcen pro studenty i vyucujici.
#   Vyuziva ostatni skripty ve slozce .vscode/.
#
# Pouziti:
#   powershell -ExecutionPolicy Bypass -File setup_project.ps1
#
# Poznamky:
#   - utils.ps1 musi byt ve stejne slozce
#   - upload_config.txt musi byt spravne nastaven
# ------------------------------------------------------------
$ScriptName    = "setup_project.ps1"
$ScriptVersion = "1.1"
$ScriptDate    = "2026-01-26"

. "$PSScriptRoot/utils.ps1"

Write-Host "$ScriptName - verze: $ScriptVersion ($ScriptDate)" @ColorInfo
Write-Host "======================================"

# Cesty ke skriptum
$wipe   = "$PSScriptRoot/wipe.ps1"
$upload = "$PSScriptRoot/upload.ps1"
$list   = "$PSScriptRoot/list.ps1"

# Kontrola existence skriptu
if (-not (Test-Path $wipe))   { Write-Host "ERROR: wipe.ps1 not found."   @ColorError; exit 1 }
if (-not (Test-Path $upload)) { Write-Host "ERROR: upload.ps1 not found." @ColorError; exit 1 }
if (-not (Test-Path $list))   { Write-Host "ERROR: list.ps1 not found."   @ColorError; exit 1 }

# ------------------------------------------------------------
# 1) Wipe
# ------------------------------------------------------------
Write-Host ""
Write-Host "STEP 1/3: Wiping device..." @ColorInfo
Write-Host "--------------------------------------"
powershell -ExecutionPolicy Bypass -File $wipe
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: wipe.ps1 failed." @ColorError
    exit 1
}

# ------------------------------------------------------------
# 2) Upload
# ------------------------------------------------------------
Write-Host ""
Write-Host "STEP 2/3: Uploading project..." @ColorInfo
Write-Host "--------------------------------------"
powershell -ExecutionPolicy Bypass -File $upload
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: upload.ps1 failed." @ColorError
    exit 1
}

# ------------------------------------------------------------
# 3) List
# ------------------------------------------------------------
Write-Host ""
Write-Host "STEP 3/3: Listing device content..." @ColorInfo
Write-Host "--------------------------------------"
powershell -ExecutionPolicy Bypass -File $list
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: list.ps1 failed." @ColorError
    exit 1
}

Write-Host ""
Write-Host "======================================" 
Write-Host "Setup complete. Device is ready." @ColorDone
Write-Host "======================================"
