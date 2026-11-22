# ------------------------------------------------------------
# Výpis obsahu MicroPython zařízení
#
# Použití:
#   powershell -ExecutionPolicy Bypass -File list.ps1
#
# Popis:
#   Tento skript zobrazí kompletní obsah MicroPython zařízení
#   ve formě stromu (adresáře / soubory) včetně velikostí souborů.
#
# Vlastnosti:
#   - Velmi rychlý výpis (jediný běh MicroPython skriptu)
#   - Rekurzivní průchod celým souborovým systémem
#   - Barevné rozlišení:
#       * adresáře (cyan)
#       * soubory (žlutě)
#       * velikosti souborů (šedě)
#   - Zarovnané velikosti pro snadné čtení
#
# Typické použití:
#   - kontrola, co je aktuálně nahráno v zařízení
#   - ověření výsledku uploadu
#   - hledání zapomenutých nebo velkých souborů
#
# Poznámky:
#   - Skript automaticky detekuje správný COM port
#   - Pokud zařízení nereaguje, provede se automatický reset
#   - Výpis je pouze informativní (nic se nemění ani nemaže)
#
# Vyžaduje:
#   - utils.ps1 ve stejné složce
#   - funkční mpremote a Python v PATH
# ------------------------------------------------------------
$ScriptName    = "list.ps1"
$ScriptVersion = "2.6"
$ScriptDate    = "2026-01-26"

. "$PSScriptRoot/utils.ps1"

Write-Host "$ScriptName - verze: $ScriptVersion ($ScriptDate)" @ColorInfo
Write-Host "--------------------------------------"

$port = Get-ReadyPort
Write-Host "Pouzivam port: " -NoNewline
Write-Host $port @ColorInfo

Write-Host "Obsah zarizeni:" @ColorInfo
Write-Host "--------------------------------------"

# Unicode znaky
$char_vert   = [char]0x2502   # │
$char_branch = [char]0x251C   # ├
$char_last   = [char]0x2514   # └
$char_line   = [char]0x2500   # ─

$BranchMid  = "$char_branch$char_line$char_line "
$BranchLast = "$char_last$char_line$char_line "
$IndentKeep = "$char_vert   "
$IndentSkip = "    "

# Sloupec, kde začínají závorky
$BracketColumn = 40

# MicroPython skript
$mpCode = @"
import os, json

def walk(p):
    result = []
    try:
        items = os.listdir(p)
    except:
        return result

    dirs = []
    files = []

    for n in items:
        full = p + '/' + n if p != '/' else '/' + n
        try:
            st = os.stat(full)
        except:
            continue

        mode = st[0]
        if mode & 0x4000:
            dirs.append(n)
        else:
            files.append((n, st[6]))

    result.append((p, dirs, files))

    for d in dirs:
        sub = p + '/' + d if p != '/' else '/' + d
        result.extend(walk(sub))

    return result

print(json.dumps(walk('/')))
"@

# Spuštění skriptu
$raw = & python -m mpremote connect $port exec "$mpCode" 2>$null | Out-String

# Extrakce JSON
$joined = ($raw -join "`n")
$start = $joined.IndexOf('[')
$end   = $joined.LastIndexOf(']')

if ($start -lt 0 -or $end -lt 0 -or $end -le $start) {
    Write-Host "ERROR" @ColorError -NoNewline
    Write-Host ": JSON blok nenalezen."
    return
}

$json = $joined.Substring($start, $end - $start + 1)
$data = $json | ConvertFrom-Json

# ------------------------------------------------------------
# STAVBA STROMU
# ------------------------------------------------------------
function Build-Tree($data) {

    $index = @{}

    foreach ($entry in $data) {
        $path  = $entry[0]
        $dirs  = $entry[1]
        $files = $entry[2]

        $index[$path] = [PSCustomObject]@{
            Path     = $path
            Name     = (Split-Path $path -Leaf)
            DirNames = $dirs
            Files    = $files
            Children = @()
        }
    }

    foreach ($path in $index.Keys) {
        $node = $index[$path]
        foreach ($d in $node.DirNames) {
            if ($path -eq "/") { $childPath = "/$d" }
            else               { $childPath = "$path/$d" }

            if ($index.ContainsKey($childPath)) {
                $node.Children += $index[$childPath]
            }
        }
    }

    return $index["/"]
}

$tree = Build-Tree $data

# ------------------------------------------------------------
# VYKRESLENÍ STROMU
# ------------------------------------------------------------
function Print-Tree($node, $prefix = "") {

    # soubory
    $fileCount = $node.Files.Count
    for ($i = 0; $i -lt $fileCount; $i++) {
        $f = $node.Files[$i]
        $isLast = ($i -eq $fileCount - 1 -and $node.Children.Count -eq 0)

        if ($isLast) { $branch = $BranchLast }
        else         { $branch = $BranchMid }

        $full = "$prefix$branch$($f[0])"
        $gapCount = $BracketColumn - $full.Length
        if ($gapCount -lt 1) { $gapCount = 1 }
        $gap = " " * $gapCount

        Write-Host "$prefix$branch" -NoNewline
        Write-Host $f[0] @ColorFile -NoNewline
        Write-Host $gap -NoNewline

        Write-Host "(" -NoNewline
        Write-Host ("{0,6} B" -f $f[1]) @ColorSize -NoNewline
        Write-Host ")"
    }

    # adresáře
    $childCount = $node.Children.Count
    for ($i = 0; $i -lt $childCount; $i++) {
        $child = $node.Children[$i]
        $isLast = ($i -eq $childCount - 1)

        if ($isLast) { $branch = $BranchLast }
        else         { $branch = $BranchMid }

        Write-Host "$prefix$branch" -NoNewline
        Write-Host ($child.Name + "/") @ColorDir

        if ($isLast) { $newPrefix = $prefix + $IndentSkip }
        else         { $newPrefix = $prefix + $IndentKeep }

        Print-Tree $child $newPrefix
    }
}

# Výpis
Print-Tree $tree ""

Write-Host "--------------------------------------"
Write-Host "Hotovo." @ColorDone
Write-Host "--------------------------------------"