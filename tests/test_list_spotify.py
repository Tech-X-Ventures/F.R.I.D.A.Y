import win32gui
import win32process
import psutil

windows = []
def callback(hwnd, extra):
    try:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        proc = psutil.Process(pid)
        if "spotify" in proc.name().lower():
            title = win32gui.GetWindowText(hwnd)
            visible = win32gui.IsWindowVisible(hwnd)
            windows.append((hwnd, title, visible, pid))
    except Exception:
        pass
    return 1

win32gui.EnumWindows(callback, None)
for w in windows:
    print(w)
