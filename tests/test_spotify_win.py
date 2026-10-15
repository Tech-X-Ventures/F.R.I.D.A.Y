import os
if os.environ.get('FRYDAY_ENABLE_LIVE_DESKTOP_TESTS') != '1':
    print('SKIP: live desktop test; set FRYDAY_ENABLE_LIVE_DESKTOP_TESTS=1 to opt in')
    raise SystemExit(0)

import os
import time
import win32gui
import win32process
import psutil

print("Launching spotify:search:starboy...")
os.system('start "" "spotify:search:starboy"')
time.sleep(3)

windows = []
def callback(hwnd, extra):
    if win32gui.IsWindowVisible(hwnd):
        title = win32gui.GetWindowText(hwnd)
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            proc = psutil.Process(pid)
            if "spotify" in proc.name().lower():
                windows.append((hwnd, title, proc.name(), pid))
        except Exception:
            pass
    return 1

try:
    win32gui.EnumWindows(callback, None)
except Exception:
    pass

print("Spotify windows found after launch:")
for w in windows:
    print(w)

