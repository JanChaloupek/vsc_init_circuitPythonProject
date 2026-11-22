# ------------------------------------------------------------
# MicroPython CLI nástroj
#
# Učel:
#   Jednotné rozhraní pro práci s MicroPython zařízeními.
#   Tento skript smeřuje příkazy na jednotlivé nástroje
#   ve složce .vscode/.
#
# Použití:
#   mpy <příkaz>
#
# Příkazy:
#   viz: mpy help
#
# Využívá:
#   - PowerShell
#   - mpremote + Python v PATH
#   - skripty ve složce .vscode/
# ------------------------------------------------------------
$ScriptName    = "mpy.ps1"
$ScriptVersion = "1.1"
$ScriptDate    = "2026-01-27"

function Show-Help {
    Write-Host "Dostupne prikazy:" @ColorInfo
    Write-Host "  upload    - nahrani celeho projektu"
    Write-Host "  main      - nahrani pouze main.py"
    Write-Host "  runmain   - spusteni main.py bez nahravani"
    Write-Host "  list      - vypis obsahu zarizeni"
    Write-Host "  check     - diagnostika zarizeni"
    Write-Host "  repl      - REPL konzole"
    Write-Host "  wipe      - smazani obsahu zarizeni"
    Write-Host "  setup     - kompletni priprava projektu"
    Write-Host "  help      - tato napoveda"
}

Write-Host "$ScriptName - verze: $ScriptVersion ($ScriptDate)"
Write-Host "--------------------------------------"

# Pokud není příkaz → zobraz help
if ($args.Count -eq 0) {
    Show-Help
    exit 0
}

$cmd  = $args[0].ToLower()
$base = "$PSScriptRoot"

switch ($cmd) {

    "check"   { powershell -ExecutionPolicy Bypass -File "$base/check.ps1" }
    "upload"  { powershell -ExecutionPolicy Bypass -File "$base/upload.ps1" }
    "main"    { powershell -ExecutionPolicy Bypass -File "$base/upload_main.ps1" }
    "runmain" { powershell -ExecutionPolicy Bypass -File "$base/run_main.ps1" }
    "repl"    { powershell -ExecutionPolicy Bypass -File "$base/repl.ps1" }
    "list"    { powershell -ExecutionPolicy Bypass -File "$base/list.ps1" }
    "wipe"    { powershell -ExecutionPolicy Bypass -File "$base/wipe.ps1" }
    "setup"   { powershell -ExecutionPolicy Bypass -File "$base/setup_project.ps1" }
    "help"    { Show-Help }

    default {
        Write-Host "Neznamy prikaz: $cmd" @ColorError
        Show-Help
        exit 1
    }
}

Write-Host "--------------------------------------"
Write-Host "Hotovo."
