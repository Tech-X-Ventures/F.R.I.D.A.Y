import win32gui

def enum_handler(hwnd, ctx):
    txt = win32gui.GetWindowText(hwnd)
    if txt:
        print(f"HWND: {hwnd} | Title: '{txt}'")
    return True

win32gui.EnumWindows(enum_handler, None)
