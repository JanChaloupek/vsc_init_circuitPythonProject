# ------------------------------------------------------------
# setup.ps1
#
# Ucel:
#   Kompletni jednorazova priprava vyvojoveho prostredi
#   pro MicroPython i CircuitPython ve VS Code:
#     1) Kontrola Pythonu (pripadna ticha instalace z python.org
#        pro aktualniho uzivatele - nepotrebuje prava spravce)
#     2) Virtualni prostredi .venv v koreni projektu
#     3) Instalace Python knihoven do .venv: mpremote (MicroPython,
#        obsahuje i pyserial) a matplotlib (graf: mpy plot / cpy plot)
#     4) Nastaveni panelu a Run on Save v settings.json
#        (zapisuje je .vscode/deska.py vscode - tlacitka jsou
#        definovana jen tam, stejne pro Windows i Linux/macOS).
#        Jde PRED instalaci rozsireni: panel si pri prvnim
#        spusteni precte uz hotova tlacitka, okno neni potreba
#        znovu nacitat. Nastaveni nepotrebuje VS Code CLI.
#     5) Detekce VS Code CLI
#     6) Instalace rozsireni MicroPython & CircuitPython Panel (.vsix)
#     7) Hromadna instalace rozsireni z Marketplace (obe platformy)
#     8) Kontrola pripojenych desek (.vscode/deska.py devices)
#
# Knihovny jdou do .venv (jen pro tento projekt), systemovy Python
# zustane cisty. deska.py si .venv najde sam, prikazy v settings.json
# proto zustavaji "python .vscode/deska.py ...".
#
# Vsechny ostatni nastroje (mpy, cpy) jsou v jedinem souboru
# .vscode/deska.py. Tento skript zustava v PowerShellu, protoze
# musi umet nainstalovat i samotny Python.
# ------------------------------------------------------------
$ScriptName    = "setup.ps1"
$ScriptVersion = "3.4"
$ScriptDate    = "2026-11-26"

# Python, ktery se nainstaluje, kdyz na pocitaci zadny neni.
# Vyzkouseno s mpremote 1.27 a matplotlib 3.11 (rada 3.14).
$PythonVersion = "3.14.10"
$PythonMin     = [version]"3.9"

# Barevne profily vypisu (drive v utils.ps1)
$ColorInfo  = @{ ForegroundColor = "Cyan" }
$ColorError = @{ ForegroundColor = "Red" }
$ColorFile  = @{ ForegroundColor = "Yellow" }
$ColorDone  = @{ ForegroundColor = "Green" }

$DeskaPy     = Join-Path $PSScriptRoot "deska.py"
$ProjectRoot = Split-Path $PSScriptRoot -Parent
$VenvDir     = Join-Path $ProjectRoot ".venv"
$VenvPy      = Join-Path $VenvDir "Scripts\python.exe"

Write-Host "============================================================" @ColorInfo
Write-Host "  $ScriptName - verze: $ScriptVersion ($ScriptDate)" @ColorInfo
Write-Host "  Kompletni priprava prostredi: MicroPython & CircuitPython" @ColorInfo
Write-Host "============================================================"
Write-Host ""

# Najde pouzitelny Python (>= $PythonMin). Vrati plnou cestu k python.exe
# a verzi, nebo $null.
# Zastupce z Microsoft Store (WindowsApps\python.exe) se pri prikazu
# s parametry ukonci chybou 9009 - tim se odfiltruje sam.
function Find-Python {
    $script = "import sys; print(sys.executable); print('%d.%d.%d' % sys.version_info[:3])"
    $candidates = @(@("python"), @("py", "-3"))
    # Cerstva instalace pro uzivatele (PATH v tomto okne nemusi byt aktualni)
    Get-ChildItem "$env:LOCALAPPDATA\Programs\Python\Python3*\python.exe" -ErrorAction SilentlyContinue |
        Sort-Object FullName -Descending | ForEach-Object { $candidates += ,@($_.FullName) }
    foreach ($cand in $candidates) {
        $exe  = $cand[0]
        $rest = @($cand | Select-Object -Skip 1)
        if (-not (Get-Command $exe -ErrorAction SilentlyContinue)) { continue }
        $out = & $exe @rest -c $script 2>$null
        if ($LASTEXITCODE -ne 0 -or @($out).Count -lt 2) { continue }
        try { $ver = [version]@($out)[1] } catch { continue }
        if ($ver -lt $PythonMin) {
            Write-Host "  (nalezen Python $ver v $(@($out)[0]) - je prilis stary, potreba $PythonMin+)" @ColorFile
            continue
        }
        return @{ Exe = @($out)[0]; Version = $ver }
    }
    return $null
}

# ------------------------------------------------------------
# 1) Check Python
# ------------------------------------------------------------
Write-Host "[1/8] Kontrola instalace Pythonu..." @ColorInfo

$PythonInstalled = $false
$python = Find-Python
if (-not $python) {
    $arch = if ($env:PROCESSOR_ARCHITECTURE -eq "ARM64") { "arm64" } else { "amd64" }
    $url = "https://www.python.org/ftp/python/$PythonVersion/python-$PythonVersion-$arch.exe"
    $installer = Join-Path $env:TEMP "python-$PythonVersion-$arch.exe"

    Write-Host "Python nenalezen. Stahuji Python $PythonVersion z python.org..." @ColorFile
    Write-Host "  $url"
    try {
        $ProgressPreference = "SilentlyContinue"     # jinak je stahovani v PowerShellu 5.1 velmi pomale
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $url -OutFile $installer -UseBasicParsing -ErrorAction Stop
    } catch {
        Write-Host "Stazeni selhalo: $($_.Exception.Message)" @ColorError
        Write-Host "Nainstalujte Python rucne z https://www.python.org/downloads/ (zaskrtnete 'Add python.exe to PATH')" @ColorError
        Write-Host "a pak spustte setup.bat znovu." @ColorError
        exit 1
    }

    # Instalace jen pro tohoto uzivatele: nepotrebuje prava spravce, takze
    # ticha instalace (/quiet) neskonci na dotazu UAC. PrependPath prida
    # Python do PATH uzivatele (pred zastupce z Microsoft Store).
    Write-Host "Instaluji Python $PythonVersion (pro aktualniho uzivatele, muze trvat par minut)..." @ColorInfo
    $proc = Start-Process -FilePath $installer -Wait -PassThru -ArgumentList `
        "/quiet InstallAllUsers=0 PrependPath=1 Include_launcher=1 InstallLauncherAllUsers=0 Include_test=0"
    Remove-Item $installer -ErrorAction SilentlyContinue
    # 3010 = hotovo, doporucen restart pocitace
    if ($proc.ExitCode -ne 0 -and $proc.ExitCode -ne 3010) {
        Write-Host "Instalace Pythonu selhala (kod $($proc.ExitCode))." @ColorError
        Write-Host "Nainstalujte Python rucne z https://www.python.org/downloads/ (zaskrtnete 'Add python.exe to PATH')" @ColorError
        Write-Host "a pak spustte setup.bat znovu." @ColorError
        exit 1
    }

    # Toto okno ma jeste puvodni PATH - nacteme novy z registru.
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
                [Environment]::GetEnvironmentVariable("Path", "User")
    $python = Find-Python
    if (-not $python) {
        Write-Host "Python se nainstaloval, ale nejde spustit. Zavrete VS Code, otevrete ho znovu a spustte setup.bat znovu." @ColorError
        exit 1
    }
    $PythonInstalled = $true
    Write-Host "Python $($python.Version) uspesne nainstalovan." @ColorDone
} else {
    Write-Host "Python OK ($($python.Version), $($python.Exe))" @ColorDone
}
$Py = $python.Exe
Write-Host "--------------------------------------"

# ------------------------------------------------------------
# 2) Virtualni prostredi .venv
# ------------------------------------------------------------
Write-Host "[2/8] Virtualni prostredi .venv (knihovny jen pro tento projekt)..." @ColorInfo

$venvOk = $false
if (Test-Path $VenvPy) {
    & $VenvPy -m pip --version >$null 2>&1
    $venvOk = ($LASTEXITCODE -eq 0)
    if (-not $venvOk) {
        # Napr. Python, ze ktereho .venv vzniklo, byl odinstalovan.
        Write-Host "Stavajici .venv nefunguje, vytvarim ho znovu..." @ColorFile
        Remove-Item $VenvDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}
if (-not $venvOk) {
    Write-Host "Vytvarim $VenvDir ..." @ColorInfo
    & $Py -m venv $VenvDir
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $VenvPy)) {
        Write-Host "Vytvoreni .venv selhalo." @ColorError
        exit 1
    }
    Write-Host ".venv vytvoreno." @ColorDone
} else {
    Write-Host ".venv OK" @ColorDone
}
Write-Host "--------------------------------------"

# ------------------------------------------------------------
# 3) Python knihovny do .venv
# ------------------------------------------------------------
Write-Host "[3/8] Kontrola Python knihoven v .venv (mpremote, matplotlib)..." @ColorInfo

& $VenvPy -c "import mpremote, serial" >$null 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "mpremote nenalezen. Instaluji pres pip..." @ColorInfo
    & $VenvPy -m pip install --disable-pip-version-check mpremote
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Instalace mpremote selhala." @ColorError
        exit 1
    }
    Write-Host "mpremote uspesne nainstalovan." @ColorDone
} else {
    Write-Host "mpremote OK" @ColorDone
}

# matplotlib je potreba jen pro graf (mpy plot / cpy plot)
& $VenvPy -c "import matplotlib" >$null 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "matplotlib (graf) nenalezen. Instaluji pres pip..." @ColorInfo
    & $VenvPy -m pip install --disable-pip-version-check matplotlib
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Instalace matplotlib selhala (graf nebude fungovat, ostatni ano)." @ColorError
    } else {
        Write-Host "matplotlib uspesne nainstalovan." @ColorDone
    }
} else {
    Write-Host "matplotlib OK" @ColorDone
}
Write-Host "--------------------------------------"

# ------------------------------------------------------------
# 4) Kontrola a nastaveni settings.json pro Windows
# ------------------------------------------------------------
Write-Host "[4/8] Nastaveni panelu a Run on Save (settings.json)..." @ColorInfo

# Tlacitka panelu i Run on Save jsou definovana v deska.py (PANEL_BUTTONS),
# aby byla stejna pro Windows i Linux/macOS.
& $Py $DeskaPy vscode
if ($LASTEXITCODE -ne 0) {
    Write-Host "  -> Upozorneni: settings.json se nepodarilo nastavit." @ColorError
}
Write-Host "--------------------------------------"

# ------------------------------------------------------------
# 5) Detekce VS Code CLI
# ------------------------------------------------------------
Write-Host "[5/8] Detekce rozhrani VS Code CLI..." @ColorInfo

$possiblePaths = @(
    "$env:LOCALAPPDATA\Programs\Microsoft VS Code\bin\code.cmd",
    "$env:LOCALAPPDATA\Programs\Microsoft VS Code Insiders\bin\code-insiders.cmd",
    "C:\Program Files\Microsoft VS Code\bin\code.cmd",
    "C:\Program Files\Microsoft VS Code\bin\code-insiders.cmd",
    "C:\Program Files\Microsoft VS Code\bin\code-arm64.cmd",
    "C:\Program Files (x86)\Microsoft VS Code\bin\code.cmd",
    "C:\Program Files (x86)\Microsoft VS Code\bin\code-insiders.cmd"
)

$codeCmd = $null
if (Get-Command "code" -ErrorAction SilentlyContinue) {
    $codeCmd = "code"
}

if (-not $codeCmd) {
    foreach ($path in $possiblePaths) {
        if (Test-Path $path) {
            $codeCmd = $path
            break
        }
    }
}

if (-not $codeCmd) {
    # Nastaveni (krok 4) uz je hotove, desky (krok 8) zkontrolujeme i tak.
    Write-Host "VS Code CLI nenalezen. Preskakuji instalaci rozsireni (kroky 6 a 7)." @ColorError
    Write-Host "  Nainstalujte VS Code z https://code.visualstudio.com a spustte setup.bat znovu." @ColorError
} else {
    Write-Host "VS Code CLI nalezen: $codeCmd" @ColorDone
}

# Testovaci prostredi lektora (OneDrive\R_D\test-infra, Start-StudentTest.ps1):
# nad slozkou projektu lezi znackovy soubor test-infra.json s cestou
# k testovaci slozce rozsireni. Rozsireni se pak instaluji tam
# (--extensions-dir), ne do bezneho VS Code lektora.
# Student tento soubor nema, pro nej se nic nemeni.
$CodeExtArgs = @()
$markerDir = Split-Path $ProjectRoot -Parent   # nad korenem projektu
for ($i = 0; $i -lt 3 -and $markerDir; $i++) {
    $marker = Join-Path $markerDir "test-infra.json"
    if (Test-Path $marker) {
        try {
            $testInfra = Get-Content $marker -Raw | ConvertFrom-Json
            if ($testInfra.extensionsDir) {
                $CodeExtArgs = @("--extensions-dir", $testInfra.extensionsDir)
                Write-Host "TESTOVACI PROSTREDI (nalezen $marker):" @ColorFile
                Write-Host "  rozsireni se instaluji do $($testInfra.extensionsDir)" @ColorFile
            }
        } catch {
            Write-Host "Upozorneni: $marker nelze precist - rozsireni pujdou do bezneho VS Code." @ColorError
        }
        break
    }
    $markerDir = Split-Path $markerDir -Parent
}
Write-Host "--------------------------------------"

# ------------------------------------------------------------
# 6) Instalace MicroPython & CircuitPython Panelu
# ------------------------------------------------------------
Write-Host "[6/8] Instalace rozsireni MicroPython & CircuitPython Panel..." @ColorInfo

# Prikaz "code" bezi na Node.js a pri instalaci rozsireni vypisuje varovani
# "DeprecationWarning: url.parse()". Neni to chyba, jen by studenta zbytecne
# vystrasilo - promenna NODE_NO_WARNINGS ho skryje (plati jen pro kroky 6 a 7).
$oldNodeNoWarnings = $env:NODE_NO_WARNINGS
$env:NODE_NO_WARNINGS = "1"

$vsix = Join-Path $PSScriptRoot "dist\micropython-panel.vsix"
if (-not $codeCmd) {
    Write-Host "Preskoceno (VS Code CLI nenalezen)." @ColorError
} elseif (Test-Path $vsix) {
    & $codeCmd @CodeExtArgs --install-extension $vsix --force
    if ($LASTEXITCODE -eq 0) {
        Write-Host "MicroPython & CircuitPython Panel uspesne nainstalovan/aktualizovan." @ColorDone
    } else {
        Write-Host "Instalace panelu selhala." @ColorError
    }
} else {
    Write-Host "Upozorneni: Balicek $vsix nebyl nalezen." @ColorError
}
Write-Host "--------------------------------------"

# ------------------------------------------------------------
# 7) Hromadne instalace rozsireni z Marketplace
# ------------------------------------------------------------
Write-Host "[7/8] Instalace spolecnych rozsireni z Marketplace..." @ColorInfo

$allExtensions = @(
    @{ Id = "ms-python.python";                            Name = "Python (jazykova podpora)" },
    @{ Id = "ms-python.vscode-pylance";                   Name = "Pylance (analyza kodu a naseptavani)" },
    @{ Id = "wmerkens.vscode-circuitpython-v2-cursor-ai";  Name = "CircuitPython podpora (0.3.3)" },
    @{ Id = "emeraldwalk.runonsave";                       Name = "Run on Save (automaticke nahravani)" },
    @{ Id = "streetsidesoftware.code-spell-checker";       Name = "Code Spell Checker" },
    @{ Id = "streetsidesoftware.code-spell-checker-czech"; Name = "Czech - Code Spell Checker" },
    @{ Id = "oderwat.indent-rainbow";                      Name = "Indent Rainbow (barevne odsazeni)" },
    @{ Id = "ms-vscode.powershell";                        Name = "PowerShell podpora" },
    @{ Id = "jebbs.plantuml";                              Name = "PlantUML (diagramy trid robota)" },
    @{ Id = "IBM.output-colorizer";                        Name = "Output Colorizer (barevne logy)" },
    @{ Id = "eugenejeon.codesnap-plus-fix";                Name = "CodeSnap-plus-fix (snimky kodu pro PR)" }
)

if (-not $codeCmd) {
    Write-Host "Preskoceno (VS Code CLI nenalezen)." @ColorError
    $allExtensions = @()
}
foreach ($ext in $allExtensions) {
    Write-Host "  -> Instaluji $($ext.Name) ... " -NoNewline
    & $codeCmd @CodeExtArgs --install-extension $ext.Id --force | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK]" @ColorDone
    } else {
        Write-Host "[CHYBA]" @ColorError
    }
}
$env:NODE_NO_WARNINGS = $oldNodeNoWarnings
Write-Host "--------------------------------------"

# ------------------------------------------------------------
# 8) Detekce pripojeneho hardware
# ------------------------------------------------------------
Write-Host "[8/8] Kontrola pripojenych desek..." @ColorInfo

# Vypise desky s CircuitPythonem (disk CIRCUITPY) i MicroPythonem (COM port).
# Kdyz neni pripojena zadna deska, nevadi to - prostredi je pripraveno.
& $Py $DeskaPy devices

# Tlacitka panelu a Run on Save spousteji prikaz "python". Overime, ze
# funguje (a neni to jen zastupce z Microsoft Store).
& python -c "import sys" >$null 2>&1
$pythonCmdOk = ($LASTEXITCODE -eq 0)

if ($codeCmd) {
    Write-Host "============================================================" @ColorDone
    Write-Host "  Instalace je KOMPLETNI! Prostredi je pripraveno." @ColorDone
    Write-Host "  Muzete pracovat s MicroPythonem i CircuitPythonem." @ColorDone
    Write-Host "============================================================" @ColorDone
} else {
    Write-Host "============================================================" @ColorError
    Write-Host "  Instalace NENI kompletni: chybi rozsireni VS Code." @ColorError
    Write-Host "  Python, knihovny a nastaveni jsou pripravene. Nainstalujte" @ColorError
    Write-Host "  VS Code (https://code.visualstudio.com) a spustte setup.bat znovu." @ColorError
    Write-Host "============================================================" @ColorError
}
if ($PythonInstalled -or -not $pythonCmdOk) {
    Write-Host ""
    Write-Host "DULEZITE: Zavrete VS Code a otevrete ho znovu." @ColorFile
    Write-Host "  VS Code si seznam programu (PATH) nacita jen pri spusteni. Dokud ho" @ColorFile
    Write-Host "  nezavrete, nenajde novy Python a nefunguje Ctrl+S ani tlacitka panelu." @ColorFile
    if (-not $pythonCmdOk -and -not $PythonInstalled) {
        Write-Host "  Kdyz to nepomuze: Nastaveni Windows -> Aplikace -> Upresnit nastaveni aplikaci" @ColorFile
        Write-Host "  -> Aliasy spousteni aplikaci -> vypnete 'python.exe' a 'python3.exe'." @ColorFile
    }
}
