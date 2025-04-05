#!/bin/bash
# Davka v Bash. Umi kopirovat soubory do disku se jmenem 'CIRCUITPY'
# (což je jméno disku CircuitPythonu, který je nainstalován v pico:ed-u)
# Verze souboru ze dne 2025-02-22

# Kontrola počtu předaných parametrů
if [ "$#" -ne 3 ]; then
    echo "Použití: $0 sourceRoot relativePath ignoreFilePath"
    exit 1
fi

sourceRoot="$1"
relativePath="$2"
ignoreFilePath="$3"

echo "----------------------------------------------------------"
echo "Spouštím kopírování souboru do Pico:ed-u. Chci zkopírovat soubor '$relativePath' v adresáři '$sourceRoot'."
echo "Zkouším načíst obsah souboru se seznamem ignorovaných položek '$ignoreFilePath'."

# Cesta k souboru se seznamem ignorovaných položek
ignoreFileFullPath="$sourceRoot/$ignoreFilePath"

if [ ! -f "$ignoreFileFullPath" ]; then
    echo "Soubor se seznamem ignorovaných souborů se mi nedaří najít. Nemůžu pokračovat v kopírování -> končím akci."
    exit 2
fi

# Načtení ignore listu do pole bez použití mapfile
ignoreList=()
while IFS= read -r line; do
    ignoreList+=("$line")
done < "$ignoreFileFullPath"

# Funkce pro kontrolu, zda je relativní cesta obsažena v ignore listu (podpora zástupných znaků)
test_is_ignored() {
    local relpath="$1"
    shift
    for pattern in "$@"; do
        # Bash porovnání s globbingem
        if [[ "$relpath" == $pattern ]]; then
            echo "$pattern"
            return 0
        fi
    done
    return 1
}

# Kontrola, zda soubor/adresář není v ignore listu
ignorePattern=$(test_is_ignored "$relativePath" "${ignoreList[@]}")
if [ $? -eq 0 ]; then
    echo "Soubor '$relativePath' je v seznamu ignorovaných podle masky '$ignorePattern'. Nebudu ho kopírovat -> končím akci."
    exit 3
fi

echo "Všechno v pořádku, teď se pokusím najít disk s pico:ed-em."

# Funkce k nalezení disku s label 'CIRCUITPY' pro OS X
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

# Sestavení úplných cest ke zdrojovému a cílovému souboru/adresáři
sourcePath="$sourceRoot/$relativePath"
destPath="$destinationRoot/$relativePath"

echo "Už vím, který soubor chci kopírovat a mám i kam ho zkopírovat. Vezmu soubor 'zdroj' a nakopíruju ho do 'cíl':"
echo "Zdroj: '$sourcePath'"
echo "Cíl: '$destPath'"

# Zkontrolujeme, zda je cesta adresář (Container) nebo soubor (Leaf)
if [ -d "$sourcePath" ]; then
    # Pokud jde o adresář, vytvoříme cílový adresář, pokud ještě neexistuje
    mkdir -p "$destPath"
else
    # Pokud jde o soubor, nejprve zajistíme, aby existoval cílový adresář
    destDir=$(dirname "$destPath")
    mkdir -p "$destDir"
    echo "Začínám kopírovat."
    cp -f "$sourcePath" "$destPath"
    
    # Kontrola, zda příkaz cp skončil chybou
    if [ $? -ne 0 ]; then
        echo "Při kopírování došlo k chybě. Návratový kód přepínám na 4."
        exit 4
    fi    
fi

echo "Vypadá to, že všechno proběhlo správně."
