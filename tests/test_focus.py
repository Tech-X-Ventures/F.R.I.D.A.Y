import os
if os.environ.get('FRYDAY_ENABLE_LIVE_DESKTOP_TESTS') != '1':
    print('SKIP: live desktop test; set FRYDAY_ENABLE_LIVE_DESKTOP_TESTS=1 to opt in')
    raise SystemExit(0)

import win32gui
import win32con
import win32process
import ctypes
import time

def focus_spotify():
    hwnds = []
    def callback(hwnd, extra):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if "spotify" in title.lower():
                hwnds.append(hwnd)
        return 1
    win32gui.EnumWindows(callback, None)
    if not hwnds:
        print("No spotify window found")
        return None
    hwnd = hwnds[0]
    print(f"Targeting HWND: {hwnd}, Title: '{win32gui.GetWindowText(hwnd)}'")
    
    # Force foreground
    ctypes.windll.user32.ShowWindow(hwnd, 9) # SW_RESTORE
    ctypes.windll.user32.SetForegroundWindow(hwnd)
    return hwnd

hwnd = focus_spotify()
print("Foreground window is:", win32gui.GetWindowText(win32gui.GetForegroundWindow()))

