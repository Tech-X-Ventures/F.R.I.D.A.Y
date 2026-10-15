' FRYDAY Silent Launcher
' Launches run.bat without showing the terminal window
' Double-click this file to start FRYDAY directly

Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
WshShell.Run "cmd /c call run.bat", 0, False
