import os
if os.environ.get('FRYDAY_ENABLE_LIVE_DESKTOP_TESTS') != '1':
    print('SKIP: live desktop test; set FRYDAY_ENABLE_LIVE_DESKTOP_TESTS=1 to opt in')
    raise SystemExit(0)

import os
import time
import win32com.client

shell = win32com.client.Dispatch("WScript.Shell")

print("1. Activating Spotify...")
res = shell.AppActivate("Spotify")
print("AppActivate:", res)

time.sleep(0.5)

# Open quick search overlay
print("2. Sending Ctrl+K...")
shell.SendKeys("^k")
time.sleep(0.5)

# Type song query
print("3. Typing song name...")
shell.SendKeys("starboy")
time.sleep(1.2)

# Press Enter to play
print("4. Pressing Enter...")
shell.SendKeys("{ENTER}")
time.sleep(0.5)

print("Check if audio started playing!")

