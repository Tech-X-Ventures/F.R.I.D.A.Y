$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$Python = Join-Path $Root 'venv\Scripts\python.exe'
$AppSpec = Join-Path $PSScriptRoot 'FRYDAY.spec'
$InstallerSource = Join-Path $PSScriptRoot 'installer_app.py'
$UninstallScript = Join-Path $PSScriptRoot 'uninstall.ps1'
$Icon = Join-Path $Root 'fryday.ico'
$Bundle = Join-Path $Root 'dist\FRYDAY'
$BuildRoot = Join-Path $Root 'build'
$Payload = Join-Path $BuildRoot 'FRYDAY-Payload.zip'
$ReleaseDir = Join-Path $Root 'release'
$SetupPath = Join-Path $ReleaseDir 'FRYDAY-Setup-0.1.0.exe'
$SetupWork = Join-Path $BuildRoot 'FRYDAY-Setup-work'

if (-not (Test-Path -LiteralPath $Python)) { throw "Project Python environment not found: $Python" }
if (-not (Test-Path -LiteralPath $InstallerSource)) { throw "Installer source missing: $InstallerSource" }
& $Python -m PyInstaller --version
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller is missing. Install it with: venv\Scripts\python.exe -m pip install pyinstaller' }

# Keep this developer's existing credentials/data in their user profile only.
$UserData = Join-Path $env:APPDATA 'FRYDAY'
New-Item -ItemType Directory -Force -Path $UserData | Out-Null
$SourceEnv = Join-Path $Root '.env'
$TargetEnv = Join-Path $UserData '.env'
if (-not (Test-Path -LiteralPath $TargetEnv) -and (Test-Path -LiteralPath $SourceEnv)) {
    Copy-Item -LiteralPath $SourceEnv -Destination $TargetEnv
    Write-Host 'Copied existing developer config to the current Windows account FRYDAY profile.'
}
$SourceData = Join-Path $Root 'data'
$TargetData = Join-Path $UserData 'data'
if (-not (Test-Path -LiteralPath $TargetData) -and (Test-Path -LiteralPath $SourceData)) {
    Copy-Item -LiteralPath $SourceData -Destination $TargetData -Recurse
    Write-Host 'Copied existing developer data to the current Windows account FRYDAY profile.'
}

Push-Location $Root
try {
    & $Python -m PyInstaller --clean --noconfirm $AppSpec
    if ($LASTEXITCODE -ne 0) { throw 'FRYDAY app packaging failed.' }
} finally {
    Pop-Location
}

if (-not (Test-Path -LiteralPath $Bundle)) { throw "PyInstaller app bundle missing: $Bundle" }
$PrivateFiles = Get-ChildItem -LiteralPath $Bundle -Force -Recurse -File | Where-Object {
    $_.Name -eq '.env' -or $_.FullName -match '\\data\\(user_profile|chat_memory)\.json$'
}
if ($PrivateFiles) { throw 'App bundle contains personal config or memory data; refusing to package it.' }

New-Item -ItemType Directory -Force -Path $BuildRoot, $ReleaseDir | Out-Null
if (Test-Path -LiteralPath $Payload) { Remove-Item -LiteralPath $Payload -Force }
Compress-Archive -Path (Join-Path $Bundle '*'), $UninstallScript -DestinationPath $Payload -CompressionLevel Optimal -Force
$PayloadEntries = & tar.exe -tf $Payload
if ($LASTEXITCODE -ne 0) { throw 'Could not inspect the generated setup payload.' }
if ($PayloadEntries | Where-Object { $_ -match '(^|/)\.env$|(^|/)data/(user_profile|chat_memory)\.json$' }) {
    throw 'Setup payload contains personal config or memory data; refusing to build.'
}

if (Test-Path -LiteralPath $SetupPath) { Remove-Item -LiteralPath $SetupPath -Force }
$AddDataPayload = "$Payload;."
$AddDataIcon = "$Icon;."
Push-Location $Root
try {
    & $Python -m PyInstaller --clean --noconfirm --onefile --windowed `
        --name 'FRYDAY-Setup-0.1.0' `
        --icon $Icon `
        --collect-all customtkinter `
        --hidden-import win32com.client `
        --hidden-import pythoncom `
        --hidden-import pywintypes `
        --add-data $AddDataPayload `
        --add-data $AddDataIcon `
        --distpath $ReleaseDir `
        --workpath $SetupWork `
        $InstallerSource
    if ($LASTEXITCODE -ne 0) { throw 'FRYDAY setup app build failed.' }
} finally {
    Pop-Location
}

if (-not (Test-Path -LiteralPath $SetupPath)) { throw "Setup output missing: $SetupPath" }
Write-Host "Built modern FRYDAY installer: $SetupPath"
Write-Host 'Install folder starts blank on every run; the user must choose it.'
Write-Host 'Verified setup payload excludes API config and personal memory files.'
