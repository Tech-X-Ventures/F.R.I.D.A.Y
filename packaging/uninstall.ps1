$ErrorActionPreference = 'Continue'
Add-Type -AssemblyName System.Windows.Forms
$choice = [System.Windows.Forms.MessageBox]::Show(
    'Uninstall FRYDAY? Your API key and FRYDAY data will be kept in your Windows profile.',
    'Uninstall FRYDAY',
    [System.Windows.Forms.MessageBoxButtons]::YesNo,
    [System.Windows.Forms.MessageBoxIcon]::Question
)
if ($choice -ne [System.Windows.Forms.DialogResult]::Yes) { exit 0 }

$InstallRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$StartMenu = Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\FRYDAY'
$DesktopShortcut = Join-Path ([Environment]::GetFolderPath('Desktop')) 'FRYDAY.lnk'
Remove-Item -LiteralPath 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\FRYDAY' -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $StartMenu -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $DesktopShortcut -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $InstallRoot -Recurse -Force -ErrorAction SilentlyContinue
