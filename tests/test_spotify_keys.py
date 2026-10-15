import os
if os.environ.get('FRYDAY_ENABLE_LIVE_DESKTOP_TESTS') != '1':
    print('SKIP: live desktop test; set FRYDAY_ENABLE_LIVE_DESKTOP_TESTS=1 to opt in')
    raise SystemExit(0)

import os
import time
import win32com.client

print("1. Launching Spotify search URI...")
os.system('start "" "spotify:search:starboy"')

time.sleep(2.0)

shell = win32com.client.Dispatch("WScript.Shell")

# Try AppActivate with variations
for target in ["Spotify Free", "Spotify Premium", "Spotify"]:
    res = shell.AppActivate(target)
    print(f"AppActivate('{target}') -> {res}")
    if res:
        break

time.sleep(0.5)
# Let's test sending keys
print("Sending keys...")
# In search results page, if cursor is in search box:
# Tab -> moves to filter/results
# Enter -> plays
shell.SendKeys("{TAB}")
time.sleep(0.2)
shell.SendKeys("{ENTER}")
time.sleep(0.5)
shell.SendKeys(" ")

print("Done testing keys.")

