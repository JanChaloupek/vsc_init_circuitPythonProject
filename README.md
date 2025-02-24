# Počáteční pracovní adresář pro projekt ve VSC s pico:ed-em
obsahuje adresáře: 
- .vscode - kde jsou soubory copy.ps1 a .ignorecopy potřebné pro nakopírování změněných souborů na pico:ed.
- lib - kde je obraz stejného adresáře z pico:ed-u (pokud potřebujete další knihovnu která se bude spouštět na pico:ed-u, patří do tohoto adresáře na pico:ed a sem dejte její kopii aby o ní VCS věděl.
- lib_vsc_only - kde jsou knihovny, které circuitPython umí sám od sebe ale VSC o nich neví. Tento adreář má vyjimku v kopírování a soubory v něm nepatří na pico:ed.
