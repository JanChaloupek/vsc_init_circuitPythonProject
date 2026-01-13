# Davka v PowerShell-u. Umi kopirovat soubory do disku se jmenem 'CIRCUITPY' (coz je jmeno disku CircuitPythonu, ktery je nainstalovany v pico:ed-u)
# Autor: Jan Chaloupek
param (
    [string]$sourceRoot,            # pracovni adresar projektu v pocitaci                        (prvni parametr)
    [string]$relativePath,          # reletivni cesta souboru, ktery chceme zkopirovat            (druhy parametr)
    [string]$ignoreFilePath         # relativni cesta k souboru se seznamem ignorovanych souboru  (treti parametr)
)
# Verze souboru:
$version = "2026-01-13"

# Přepneme kodovani na UTF-8, aby se spravne zobrazoaly ceske znaky
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Funkce hledá ve Windows disk se jménem 'CIRCUITPY'
function Find-CircuitPYDrive {
    $drives = Get-WmiObject Win32_LogicalDisk | Where-Object { $_.VolumeName -eq 'CIRCUITPY' }
    $drivesCount = $drives | Measure-Object | Select-Object -ExpandProperty Count
    if ($drivesCount -eq 1) {
        return ${drives}.DeviceID
    } elseif ($drivesCount -gt 1) {
        return ${drives}[0].DeviceID
    } else {
        Write-Host "Error: Nenasel jsem disk se jmenem 'CIRCUITPY'. Nemam kam soubor nakopirovat -> koncim akci."
        exit 1
    }
}

Write-Host "-------(verze=$version)-----------------------------------------------"
Write-Host "Spoustim kopirovani souboru do Picoed-u. Chci zkopirovat soubor '$relativePath' v adresari '$sourceRoot'."
Write-Host "Zkousim nacist obsah souboru se seznamem ignorovanych polozek '$ignoreFilePath'."

# Load ignore list
$ignoreFileFullPath = Join-Path -Path $sourceRoot -ChildPath $ignoreFilePath
if (!(Test-Path $ignoreFileFullPath -PathType Leaf)) {
    Write-Host "Error: Soubor se seznamem ignorovanych souboru se mi nedari najit. Nemuzu pokracovat v kopirovani -> koncim akci."
    exit 2

}

# Load ignore list
$ignoreList = Get-Content -Path $ignoreFileFullPath
# Check if the file or directory is in the ignore list (support for wildcards)
function Test-IsIgnored($relativePath, $ignoreList, [ref]$ignorePattern) {
    foreach ($pattern in $ignoreList) {
        if ($relativePath -like $pattern) {
            $ignorePattern.Value = $pattern
            return $true
        }
    }
    return $false
}

# ------------------------------------------------------------
# Funkce pro kontrolu, zda je relativní cesta v ignore listu
# ------------------------------------------------------------
function Test-IsIgnored {
    param(
        [string]$relativePath,
        [string[]]$patterns
    )

    # Normalizace cesty: Windows "\" → POSIX "/"
    $normalized = $relativePath -replace '\\','/'

    foreach ($pattern in $patterns) {

        # Normalizace masky
        $p = $pattern -replace '\\','/'

        # PowerShell neumí ** → nahradíme ho za *
        # (funguje pro účely ignorování celých stromů)
        $p = $p -replace '\*\*','*'

        # Porovnání
        if ($normalized -like $p) {
            return $pattern
        }
    }

    return $null
}

#$ignorePattern = ''
$ignorePattern = Test-IsIgnored $relativePath $ignoreList
if ($ignorePattern) {
    Write-Host "Error: Soubor '$relativePath' je ignorován podle masky '$ignorePattern'. Nebudu ho kopírovat -> koncim akci."
    exit 3
}

Write-Host "Soubor neni v seznamu k ignorovani. Ted se pokusim najit v OS disk s picoed-em."
$destinationRoot = Find-CircuitPYDrive
Write-Host "Nasel jsem. Disk s picoed-em je na '$destinationRoot'."

# Pokud je zadaná cesta absolutní (plná), necháme ji beze změny, jinak ji převedeme na úplnou
if ([System.IO.Path]::IsPathRooted($relativePath)) {
    $sourcePath = $relativePath
} else {
    $sourcePath = Join-Path -Path $sourceRoot -ChildPath $relativePath
}
$destPath = Join-Path -Path $destinationRoot -ChildPath $relativePath
Write-Host "Uz mam platny soubor, ktery chci zkopirovat, a mam ho i kam zkopirovat. Vezmu soubor 'zdroj' a nakopiruju ho do 'cil'"
Write-Host "      zdroj: '$sourcePath'"
Write-Host "      cil: '$destPath'"

# Check if it's a directory or a file
if (Test-Path $sourcePath -PathType Container) {
    # It's a directory, create it if needed
    if (!(Test-Path $destPath)) {
        New-Item -ItemType Directory -Path $destPath -Force | Out-Null
        Write-Host "Vytvoren cilovy adresar: '$destPath'"
    }
} else {
    # It's a file, make sure the directory exists first
    $destDir = Split-Path -Path $destPath -Parent
    if (!(Test-Path $destDir)) {
        New-Item -ItemType Directory -Path $destDir -Force | Out-Null
        Write-Host "Vytvoren cilovy adresar: '$destDir'"
    }

    # Check if source and destination paths are the same
    if ($sourcePath -eq $destPath) {
        Write-Host "Info: Zdroj a cilova cesta jsou stejne. Preskakuji kopirovani."
    } else {
        Write-Host "Zacinam kopirovat."
        try {
            Copy-Item -Path $sourcePath -Destination $destPath -Force
            Write-Host "Info: Vypada to, ze vsechno probehlo spravne."
        } catch {
            Write-Host "Error: Kopirovani neprobehlo uspesne."
            Write-Host "Error:" $_.Exception.Message
            exit 4
        }
    }
}
