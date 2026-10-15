taskkill /f /im explorer.exe
Start-Sleep -Milliseconds 800
$cache1 = Join-Path $env:LOCALAPPDATA "IconCache.db"
$explorerCache = Join-Path $env:LOCALAPPDATA "Microsoft\Windows\Explorer"
Remove-Item $cache1 -Force -ErrorAction SilentlyContinue
Get-ChildItem $explorerCache -Filter "iconcache_*.db" -ErrorAction SilentlyContinue | Remove-Item -Force
Start-Process explorer.exe
Write-Host "Icon cache cleared! Explorer restarted."

