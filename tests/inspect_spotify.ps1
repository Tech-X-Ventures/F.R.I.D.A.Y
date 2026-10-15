Add-Type @'
using System;
using System.Runtime.InteropServices;
using System.Text;

public class Win32 {
    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);
    [DllImport("user32.dll")]
    public static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);
    [DllImport("user32.dll")]
    public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);
    [DllImport("user32.dll")]
    public static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);
    [DllImport("user32.dll")]
    public static extern int GetClassName(IntPtr hWnd, StringBuilder lpClassName, int nMaxCount);
    [DllImport("user32.dll")]
    public static extern bool IsWindowVisible(IntPtr hWnd);
}
'@

$spotifyPids = (Get-Process Spotify -ErrorAction SilentlyContinue).Id
[Win32]::EnumWindows({
    param($hwnd, $lparam)
    [uint32]$procId = 0
    [Win32]::GetWindowThreadProcessId($hwnd, [ref]$procId)
    if ($spotifyPids -contains $procId) {
        $sb = New-Object System.Text.StringBuilder 256
        [Win32]::GetWindowText($hwnd, $sb, 256) | Out-Null
        $title = $sb.ToString()
        $sbClass = New-Object System.Text.StringBuilder 256
        [Win32]::GetClassName($hwnd, $sbClass, 256) | Out-Null
        $class = $sbClass.ToString()
        $vis = [Win32]::IsWindowVisible($hwnd)
        if ($title -ne "" -or $vis) {
            Write-Host "HWND: $hwnd | PID: $procId | Class: $class | Vis: $vis | Title: '$title'"
        }
    }
    return $true
}, [IntPtr]::Zero)
