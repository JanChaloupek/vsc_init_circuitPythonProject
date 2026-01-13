#!/bin/bash
# Kopírování souborů do CIRCUITPY (macOS/Linux)
version="2026-01-13"

shopt -s globstar nullglob

if [ "$#" -ne 3 ]; then
    echo "Použití: $0 sourceRoot relativePath ignoreFilePath"
    exit 1
fi

sourceRoot="$1"
relativePath="$2"
ignoreFilePath="$3"

echo "-------(verze=$version)-----------------------------------------------"
echo "Spouštím kopírování souboru do Pico:ed-u. Chci zkopírovat soubor '$relativePath' v adresáři '$sourceRoot'."
echo "Zkouším načíst obsah souboru se seznamem ignorovaných položek '$ignoreFilePath'."

ignoreFileFullPath="$sourceRoot/$ignoreFilePath"

if [ ! -f "$ignoreFileFullPath" ]; then
    echo "Soubor se seznamem ignorovaných souborů se mi nedaří najít. Nemůžu pokračovat v kopírování -> končím akci."
    exit 2
fi

# Načtení ignore listu
ignoreList=()
while IFS= read -r line; do
    ignoreList+=("$line")
done < "$ignoreFileFullPath"

# Funkce pro kontrolu ignorování
test_is_ignored() {
    local relpath="$1"
    shift
    for pattern in "$@"; do
        # Bash globbing — funguje i s **
        if [[ "$relpath" == $pattern ]]; then
            echo "$pattern"
            return 0
        fi
    done
    return 1
}

# Test ignorování
ignorePattern=$(test_is_ignored "$relativePath" "${ignoreList[@]}")
if [ $? -eq 0 ]; then
    echo "Soubor '$relativePath' je v seznamu ignorovaných podle masky '$ignorePattern'. Nebudu ho kopírovat -> končím akci."
    exit 3
fi

echo "Všechno v pořádku, teď se pokusím najít disk s pico:ed-em."

# Najdi CIRCUITPY
find_circuitpy_drive() {
    if [ -d "/Volumes/CIRCUITPY" ]; then
        echo "/Volumes/CIRCUITPY"
    else
        echo "Nenašel jsem disk se jménem 'CIRCUITPY'. Nemám tedy kam soubor nakopírovat -> končím akci." >&2
        exit 1
    fi
}

destinationRoot=$(find_circuitpy_drive)
echo "Našel jsem. Disk s pico:ed-em je na '$destinationRoot'."

# Sestavení cest
sourcePath="$sourceRoot/$relativePath"
destPath="$destinationRoot/$relativePath"

echo "Už vím, který soubor chci kopírovat a mám i kam ho zkopírovat."
echo "Zdroj: '$sourcePath'"
echo "Cíl:   '$destPath'"

# Pokud je to adresář
if [ -d "$sourcePath" ]; then
    if [ ! -d "$destPath" ]; then
        mkdir -p "$destPath"
        echo "Vytvořen cílový adresář: '$destPath'"
    fi
else
    # Pokud je to soubor
    destDir=$(dirname "$destPath")
    if [ ! -d "$destDir" ]; then
        mkdir -p "$destDir"
        echo "Vytvořen cílový adresář: '$destDir'"
    fi

    echo "Začínám kopírovat."
    cp -f "$sourcePath" "$destPath"

    if [ $? -ne 0 ]; then
        echo "Při kopírování došlo k chybě. Návratový kód přepínám na 4."
        exit 4
    fi
fi

echo "Vypadá to, že všechno proběhlo správně."
