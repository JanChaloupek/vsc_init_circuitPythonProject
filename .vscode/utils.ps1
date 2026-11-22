# ------------------------------------------------------------
# utils.ps1 - Spolecne funkce pro MicroPython skripty
# Verze: 3.1
# Datum: 2026-01-26
#
# Popis:
#   Tento soubor obsahuje sdilene funkce pro vsechny PowerShell
#   skripty pracujici s MicroPython zarizenim.
#
# Obsahuje:
#   - Konfiguraci VID/PID desky
#   - Automatickou detekci spravneho COM portu
#   - Test, zda zarizeni reaguje
#   - Bezpecny reset s cekanim
#   - Funkci Get-ReadyPort() pro pripravu zarizeni
#
# Tento soubor musi byt ve stejne slozce jako ostatni skripty.
# ------------------------------------------------------------

# ------------------------------------------------------------
# Podpora více MicroPython zařízení (Pico, ESP32-S2/S3, ESP8266…)
# ------------------------------------------------------------
$SUPPORTED_DEVICES = @(
    @{ VID = "2e8a"; PID = "000a"; Name = "ELECFREAKS Pico:ed (MicroPython)" },
    @{ VID = "2e8a"; PID = "0005"; Name = "Raspberry Pi Pico / Pico W" },
    @{ VID = "303a"; PID = "1001"; Name = "ESP32-S2" },
    @{ VID = "303a"; PID = "1002"; Name = "ESP32-S3" },
    @{ VID = "303a"; PID = "1003"; Name = "ESP32-C3" },
    @{ VID = "303a"; PID = "1004"; Name = "ESP32-C6" },
    @{ VID = "303a"; PID = "1005"; Name = "ESP32-H2" },
    @{ VID = "2886"; PID = "0046"; Name = "Seeed XIAO RP2040" },
    @{ VID = "239A"; PID = "00F1"; Name = "Adafruit Feather RP2040" },
    @{ VID = "0d28"; PID = "0204"; Name = "BBC micro:bit" }
)

function Get-MicroPythonPort {

    $devs = python -m mpremote devs 2>$null

    if (-not $devs) {
        Write-Host "ERROR" @ColorError -NoNewline
        Write-Host ": mpremote nenasel zadna zarizeni."
        exit 1
    }

    foreach ($device in $SUPPORTED_DEVICES) {
        $pattern = "$($device.VID):$($device.PID)"

        $match = $devs | Select-String $pattern | Select-Object -First 1

        if ($match) {
            $port = ($match -split "\s+")[0]
            Write-Host "Detected device: $($device.Name) on $port" @ColorInfo
            return $port
        }
    }

    Write-Host "ERROR" @ColorError -NoNewline
    Write-Host ": Nepodarilo se najit podporovane MicroPython zarizeni."
    exit 1
}

function Test-MicroPython($port) {
    python -m mpremote connect $port exec "1" 1>$null 2>$null
    return ($LASTEXITCODE -eq 0)
}

function Reset-MicroPython($port) {
    Write-Host "Provadim reset zarizeni..." @ColorInfo
    python -m mpremote connect $port reset 1>$null 2>$null
    Start-Sleep -Milliseconds 1500
}

function Get-ReadyPort {
    $port = Get-MicroPythonPort

    if (Test-MicroPython $port) {
        return $port
    }

    Reset-MicroPython $port

    if (Test-MicroPython $port) {
        return $port
    }

    Write-Host "ERROR" @ColorError -NoNewline
    Write-Host ": Zarizeni nereaguje ani po resetu."
    Write-Host "       Ujistete se, ze:" 
    Write-Host "       - neni otevreny REPL v jinem okne"
    Write-Host "       - neni spusteny Thonny / Mu / jiny editor"
    Write-Host "       - mpremote neni pripojen jinde"
    Write-Host "       - COM port neni zamceny systemem"
    exit 1
}

# ------------------------------------------------------------
# Barevné profily pro všechny skripty
# ------------------------------------------------------------
# Tmavé barvy:  Black, DarkBlue, DarkGreen, DarkCyan, DarkRed, DarkMagenta, DarkYellow, Gray
# Světlé barvy: DarkGray, Blue, Green, Cyan, Red, Magenta, Yellow, White
$ColorInfo  = @{ ForegroundColor = "Cyan" }
$ColorError = @{ ForegroundColor = "Red" }
$ColorFile  = @{ ForegroundColor = "Yellow" }
$ColorDir   = @{ ForegroundColor = "Magenta" }
$ColorSize  = @{ ForegroundColor = "DarkGray" }
$ColorDone  = @{ ForegroundColor = "Green" }
