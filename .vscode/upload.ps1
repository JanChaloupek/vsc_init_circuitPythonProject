# ------------------------------------------------------------
# Nahraje soubory na MicroPython zařízení
#
# Použití:
#   1) Upravte soubor upload_config.txt
#      - každý řádek = soubor nebo adresář k nahrání
#      - prázdné řádky a řádky začínající # se ignorují
#
#   2) Spuštění:
#      powershell -ExecutionPolicy Bypass -File upload.ps1
#
# Popis:
#   Tento skript nahraje vybrané soubory a adresáře z počítače
#   do MicroPython zařízení podle seznamu v upload_config.txt.
#
# Vlastnosti:
#   - Nahrává pouze položky uvedené v konfiguraci
#   - Automatická detekce správného COM portu
#   - Automatický reset zařízení, pokud nereaguje
#   - Barevné rozlišení:
#       * adresáře (cyan)
#       * soubory (žlutě)
#       * chybové hlášky (červeně)
#
# Typické použití:
#   - nahrání projektu do zařízení
#   - aktualizace vybraných souborů
#   - příprava zařízení na výuku nebo testování
#
# Poznámky:
#   - Skript nic nemaže, pouze nahrává
#   - Existující soubory v zařízení mohou být přepsány
#   - Cesty v upload_config.txt jsou relativní k aktuální složce
#
# Vyžaduje:
#   - utils.ps1 ve stejné složce
#   - upload_config.txt s konfigurací
#   - funkční mpremote a Python v PATH
# ------------------------------------------------------------
$ScriptName    = "upload.ps1"
$ScriptVersion = "2.6"
$ScriptDate    = "2026-01-26"

. "$PSScriptRoot/utils.ps1"

Write-Host "$ScriptName - verze: $ScriptVersion ($ScriptDate)" @ColorInfo
Write-Host "--------------------------------------"

$port = Get-ReadyPort
Write-Host "Budu pouzivat port: " -NoNewline
Write-Host $port @ColorInfo

$config = "$PSScriptRoot/upload_config.txt"
if (-not (Test-Path $config)) {
    Write-Host "ERROR" @ColorError -NoNewline
    Write-Host ": Nenalezen soubor upload_config.txt s konfiguraci."
    exit 1
}

$items = Get-Content $config | Where-Object {
    $_.Trim() -ne "" -and -not $_.StartsWith("#")
}

Write-Host "--------------------------------------"

foreach ($item in $items) {

    if (-not (Test-Path $item)) {
        Write-Host "ERROR" @ColorError -NoNewline
        Write-Host ": Preskakuji (nenalezeno): $item"
        continue
    }

    if (Test-Path $item -PathType Container) {
        Write-Host "Nahravam adresar: " -NoNewline
        Write-Host $item @ColorDir
        python -m mpremote connect $port cp -r $item ":"
    }
    else {
        Write-Host "Nahravam soubor: " -NoNewline
        Write-Host $item @ColorFile
        python -m mpremote connect $port cp $item ":"
    }
}

Write-Host "--------------------------------------"
Write-Host "Nahravani dokonceno." @ColorDone
Write-Host "--------------------------------------"
