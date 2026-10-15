$WshShell = New-Object -ComObject WScript.Shell
$Desktop = [System.Environment]::GetFolderPath('Desktop')
$ShortcutPath = "$Desktop\FRYDAY.lnk"
# Remove old shortcut if exists
if (Test-Path $ShortcutPath) {
    Remove-Item $ShortcutPath -Force
}
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = 'wscript.exe'
# Quote the argument path properly
$Shortcut.Arguments = '"D:\Personal\jarvis-assistant\FRYDAY.vbs"'
$Shortcut.WorkingDirectory = 'D:\Personal\jarvis-assistant'
$Shortcut.IconLocation = 'D:\Personal\jarvis-assistant\fryday.ico,0'
$Shortcut.Description = 'FRYDAY - AI Desktop Assistant by Prateek Sharma'
$Shortcut.WindowStyle = 7
$Shortcut.Save()
Write-Host "Desktop shortcut (FRYDAY) created/updated with new icon."
