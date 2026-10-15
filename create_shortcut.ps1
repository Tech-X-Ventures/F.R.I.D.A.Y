$WshShell = New-Object -ComObject WScript.Shell
$Desktop = [System.Environment]::GetFolderPath('Desktop')
$Shortcut = $WshShell.CreateShortcut("$Desktop\FRYDAY.lnk")
$Shortcut.TargetPath = 'wscript.exe'
$Shortcut.Arguments = '"D:\Personal\jarvis-assistant\FRYDAY.vbs"'
$Shortcut.WorkingDirectory = 'D:\Personal\jarvis-assistant'
$Shortcut.IconLocation = 'D:\Personal\jarvis-assistant\fryday.ico,0'
$Shortcut.Description = 'FRYDAY - AI Desktop Assistant by Prateek Sharma'
$Shortcut.WindowStyle = 7
$Shortcut.Save()
Write-Host "Desktop shortcut created!"
