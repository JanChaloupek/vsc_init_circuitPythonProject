# Davka v PowerShell-u. Umi kopirovat soubory do disku se jmenem 'CIRCUITPY' (coz je jmeno disku CircuitPythonu, ktery je nainstalovany v pico:ed-u)
# Verze souboru ze dne 2025-02-22
param (
    [string]$sourceRoot,            # pracovni adresar projektu v pocitaci                        (prvni parametr)
    [string]$relativePath,          # reletivni cesta souboru, ktery chceme zkopirovat            (druhy parametr)
    [string]$ignoreFilePath         # relativni cesta k souboru se seznamem ignorovanych souboru  (treti parametr)
)

# Funckce hleda ve Windows disk se jmenem 'CIRCUITPY'
function Find-CircuitPYDrive {
    $drives = Get-WmiObject Win32_LogicalDisk | Where-Object { $_.VolumeName -eq 'CIRCUITPY' }
    $drivesCount = $drives | Measure-Object | Select-Object -ExpandProperty Count
    if ($drivesCount -eq 1) {
        return ${drives}.DeviceID
    } elseif ($drivesCount -gt 1) {
        return ${drives}[0].DeviceID
    } else {
        Write-Host "Nenasel jsem disk se jmenem 'CIRCUITPY'. Nemam tedy kam soubor nakopirovat -> koncim akci."
        Write-Host ""
        Write-Error "Error1: Disc not found"
        exit 1
    }
}

Write-Host "----------------------------------------------------------"
Write-Host "Spoustim kopirovani souboru do Pico:ed-u. Chci zkopirovat soubor '$relativePath' v adresari '$sourceRoot'."
Write-Host "Zkousim nacist obsah souboru se seznamem ignorovanych polozek '$ignoreFilePath'."

# Load ignore list
$ignoreFileFullPath = Join-Path -Path $sourceRoot -ChildPath $ignoreFilePath
if (!(Test-Path $ignoreFileFullPath -PathType Leaf)) {
    Write-Host "Soubor se seznamem ignrovanych souboru se mi nedari najit. Nemuzu pokracovat v kopirovani -> koncim akci."
    Write-Host ""
    Write-Error "Error2: File with ignore list not found"
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

$ignorePattern = ''
if (Test-IsIgnored $relativePath $ignoreList ([ref]$ignorePattern)) {
    Write-Host "Soubor '$relativePath' je v seznamu ignorovanych podle masky '$ignorePattern'. Nebudu ho kopirovat -> koncim akci."
    Write-Host ""
    Write-Error "Error3: File in ignore list"
    exit 3
}

Write-Host "Vsechno v poradu, ted se pokusim najit ve Windows disk s pico:ed-em."
$destinationRoot = Find-CircuitPYDrive
Write-Host "Nasel jsem. Disk s pico:ed-em je na '$destinationRoot'."


$sourcePath = Join-Path -Path $sourceRoot -ChildPath $relativePath
$destPath = Join-Path -Path $destinationRoot -ChildPath $relativePath
Write-Host "Uz vim ktery soubor chci kopirovat a mam i kam ho zkopirovat. Vezmu soubor 'zdroj' a nakopiruju ho do 'cil'"
Write-Host "Zdroj: '$sourcePath'"
Write-Host "Cil: '$destPath'"

# Check if it's a directory or a file
if (Test-Path $sourcePath -PathType Container) {
    # It's a directory, create it if needed
    if (!(Test-Path $destPath)) {
        New-Item -ItemType Directory -Path $destPath -Force
    }
} else {
    # It's a file, make sure the directory exists first
    $destDir = Split-Path -Path $destPath -Parent
    if (!(Test-Path $destDir)) {
        New-Item -ItemType Directory -Path $destDir -Force
    }
    Write-Host "Zacinam kopirovat."
    Copy-Item -Path $sourcePath -Destination $destPath -Force
}

Write-Host "Vypada to ze vsechno probehlo spravne."
