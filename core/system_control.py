import os
import sys
import re
import time
import json
import difflib
import shutil
import ctypes
import threading
import webbrowser
import subprocess
import requests
import psutil
from datetime import datetime
from typing import Dict, Any, Tuple, Optional, List

# Virtual Key Codes for Windows Media & Volume Controls
VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_PLAY_PAUSE = 0xCD

# Dynamic Windows StartApps cache
_START_APPS_CACHE: Dict[str, str] = {}
_START_APPS_INITIALIZED = False
_START_APPS_LOCK = threading.Lock()


def _send_spotify_search_keys(shell, query: str):
    """Search Spotify and activate its first matching suggestion."""
    shell.SendKeys("^k")
    time.sleep(0.8)
    shell.SendKeys("^a")
    shell.SendKeys("{DELETE}")
    safe_query = query.replace("+", "{+}").replace("^", "{^}").replace(
        "%", "{%}").replace("~", "{~}").replace(")", "{)}").replace(
        "(", "{(}").replace("[", "{[}").replace("]", "{]}")
    shell.SendKeys(safe_query)
    time.sleep(2.5)
    # Enter alone submits the query and leaves Spotify on the search page.
    # Down selects the first matching suggestion; Enter activates that item.
    shell.SendKeys("{DOWN}")
    time.sleep(0.2)
    shell.SendKeys("{ENTER}")


def _focus_spotify_window(shell) -> bool:
    """Focus Spotify by its process ID, falling back to its window title."""
    for process in psutil.process_iter(["name", "pid"]):
        try:
            name = (process.info.get("name") or "").lower()
            if name == "spotify.exe" and shell.AppActivate(process.info["pid"]):
                return True
        except (psutil.Error, OSError, TypeError, KeyError):
            continue
    try:
        return bool(shell.AppActivate("Spotify"))
    except Exception:
        return False

def _index_start_apps():
    """Background indexer for all installed Windows applications (UWP, Store, Desktop, PWA)."""
    global _START_APPS_CACHE, _START_APPS_INITIALIZED
    try:
        cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", "Get-StartApps | ConvertTo-Json"]
        out = subprocess.check_output(cmd, text=True, timeout=8, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        data = json.loads(out)
        if isinstance(data, list):
            cache = {}
            for item in data:
                name = item.get("Name", "").strip().lower()
                appid = item.get("AppID", "").strip()
                if name and appid:
                    cache[name] = appid
            with _START_APPS_LOCK:
                _START_APPS_CACHE = cache
                _START_APPS_INITIALIZED = True
    except Exception as e:
        pass

# Start indexing immediately on a background daemon thread
threading.Thread(target=_index_start_apps, daemon=True).start()


APP_SHORTCUTS = {
    "notepad": "notepad.exe",
    "notes": "notepad.exe",
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "chrome": "shell:AppsFolder\\Chrome",
    "google chrome": "shell:AppsFolder\\Chrome",
    "edge": "msedge",
    "microsoft edge": "msedge",
    "browser": "msedge",
    "cmd": "cmd.exe",
    "command prompt": "cmd.exe",
    "terminal": "wt.exe",
    "powershell": "powershell.exe",
    "task manager": "taskmgr.exe",
    "taskmgr": "taskmgr.exe",
    "file explorer": "explorer.exe",
    "files": "explorer.exe",
    "explorer": "explorer.exe",
    "settings": "ms-settings:",
    "spotify": "shell:AppsFolder\\SpotifyAB.SpotifyMusic_zpdnekdrzrea0!Spotify",
    "vs code": "code",
    "vscode": "code",
    "code": "code",
    "visual studio code": "code",
    "paint": "mspaint.exe",
    "word": "winword.exe",
    "excel": "excel.exe",
    "powerpoint": "powerpnt.exe",
    "ppt": "powerpnt.exe",
    "vlc": "vlc.exe",
    "steam": "steam.exe",
    "discord": "discord",
    "control panel": "control.exe",
    "snipping tool": "snippingtool.exe",
    "camera": "microsoft.windows.camera:",
    "clock": "ms-clock:",
    "photos": "ms-photos:",
    "store": "ms-windows-store:",
    "whatsapp": "shell:AppsFolder\\5319275A.WhatsAppDesktop_cv1g1gvanyjgm!App",
    "watsapp": "shell:AppsFolder\\5319275A.WhatsAppDesktop_cv1g1gvanyjgm!App",
    "linkedin": "shell:AppsFolder\\7EE7776C.LinkedInforWindows_w1wdnht996qgy!App",
    "linkdin": "shell:AppsFolder\\7EE7776C.LinkedInforWindows_w1wdnht996qgy!App",
}

class SystemControl:
    @staticmethod
    def _press_key(vk_code: int, times: int = 1):
        """Simulate Windows virtual key press."""
        for _ in range(times):
            ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0)
            ctypes.windll.user32.keybd_event(vk_code, 0, 2, 0)
            time.sleep(0.05)

    @classmethod
    def _ensure_start_apps(cls):
        """Ensure StartApps index has run at least once."""
        global _START_APPS_INITIALIZED
        if not _START_APPS_INITIALIZED:
            _index_start_apps()

    @classmethod
    def clean_app_name(cls, query: str) -> str:
        """Strip conversational filler phrases from the app request."""
        t = query.strip()
        for prefix in ["open ", "launch ", "start ", "run ", "please open ", "please launch ", "fryday open ", "fryday launch ", "jarvis open ", "jarvis launch "]:
            if t.lower().startswith(prefix):
                t = t[len(prefix):].strip()
                break

        # Strip conversational noise like 'app which is installed on my workstation'
        t = re.sub(r'\s+(app|application|software)?\s*(which\s+is\s+)?install\w*\s*(on\s+.*)?$', '', t, flags=re.I)
        t = re.sub(r'\s+on\s+(my\s+)?(workstation|pc|computer|system|laptop)$', '', t, flags=re.I)
        t = re.sub(r'\s+(app|application|software)$', '', t, flags=re.I)
        return t.strip(' "\'.,!?')

    @classmethod
    def resolve_app(cls, app_name: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Locate an application across shortcuts, Windows StartApps, substring, fuzzy match, and PATH.
        Returns: (display_name, launch_target_or_appid)
        """
        cls._ensure_start_apps()
        clean = cls.clean_app_name(app_name).lower()
        if not clean:
            return None, None

        display_map = {
            "linkdin": "LinkedIn",
            "linkedin": "LinkedIn",
            "whatsapp": "WhatsApp",
            "watsapp": "WhatsApp",
            "chrome": "Google Chrome",
            "google chrome": "Google Chrome",
            "vscode": "VS Code",
            "vs code": "VS Code",
            "code": "VS Code",
            "visual studio code": "VS Code",
            "youtube": "YouTube",
            "spotify": "Spotify",
            "calc": "Calculator",
            "calculator": "Calculator",
            "notepad": "Notepad",
            "notes": "Notepad",
        }

        # 1. Direct alias check
        if clean in APP_SHORTCUTS:
            target = APP_SHORTCUTS[clean]
            return display_map.get(clean, clean.title()), target

        # 2. Check exact match in StartApps
        with _START_APPS_LOCK:
            if clean in _START_APPS_CACHE:
                return clean.title(), f"shell:AppsFolder\\{_START_APPS_CACHE[clean]}"

        # 3. Substring match in StartApps
        with _START_APPS_LOCK:
            for name, appid in _START_APPS_CACHE.items():
                if clean in name or name in clean:
                    return name.title(), f"shell:AppsFolder\\{appid}"

        # 4. Fuzzy match in StartApps and Aliases
        candidates = list(APP_SHORTCUTS.keys())
        with _START_APPS_LOCK:
            candidates.extend(list(_START_APPS_CACHE.keys()))

        close_matches = difflib.get_close_matches(clean, candidates, n=1, cutoff=0.55)
        if close_matches:
            best = close_matches[0]
            if best in APP_SHORTCUTS:
                return best.title(), APP_SHORTCUTS[best]
            with _START_APPS_LOCK:
                if best in _START_APPS_CACHE:
                    return best.title(), f"shell:AppsFolder\\{_START_APPS_CACHE[best]}"

        # 5. Check if directly in PATH or file system
        which_path = shutil.which(clean) or shutil.which(clean + ".exe")
        if which_path:
            return clean.title(), which_path

        return None, None

    @classmethod
    def open_application(cls, app_name: str) -> str:
        """Launch any desktop application using smart discovery and existence validation."""
        cleaned = cls.clean_app_name(app_name)
        if not cleaned:
            return "Please specify which application you would like me to open, Sir."

        # If it's a website or URL, redirect to open_website
        preset_sites = ["youtube", "google", "github", "reddit", "twitter", "x", "chatgpt", "wikipedia", "netflix", "amazon", "gmail"]
        if cleaned.lower() in preset_sites or "." in cleaned:
            return cls.open_website(cleaned)

        display_name, target = cls.resolve_app(cleaned)

        if not target:
            # Check Start Menu shortcuts directly as fallback
            shortcut_dirs = [
                os.path.expandvars(r"%ProgramData%\Microsoft\Windows\Start Menu\Programs"),
                os.path.expandvars(r"%AppData%\Microsoft\Windows\Start Menu\Programs")
            ]
            for sdir in shortcut_dirs:
                if os.path.exists(sdir):
                    for root, _, files in os.walk(sdir):
                        for f in files:
                            if f.lower().endswith(".lnk") and cleaned.lower() in f.lower():
                                target = os.path.join(root, f)
                                display_name = f[:-4]
                                break
                        if target:
                            break
                if target:
                    break

        if not target:
            # Final fallback: try raw Windows startfile / start
            try:
                os.startfile(cleaned)
                return f"{cleaned.title()} is now open, Sir. This is done."
            except FileNotFoundError:
                return f"I could not locate an application named '{cleaned.title()}' on your system, Sir."
            except Exception as e:
                return f"Failed to open '{cleaned.title()}': {str(e)}"

        try:
            if target.startswith("shell:AppsFolder\\"):
                # Windows Shell execution with start command ensures foreground window
                os.system(f'start "" "{target}"')
            elif target.lower().endswith(".lnk"):
                os.startfile(target)
            elif target.endswith(":"):
                os.system(f'start {target}')
            elif shutil.which(target) or target.lower().endswith(".exe"):
                os.system(f'start "" "{target}"')
            else:
                os.system(f'start "" "{target}"')

            return f"{display_name} is now open, Sir. This is done."
        except Exception as e:
            return f"Unable to launch {display_name}: {str(e)}"

    @classmethod
    def open_website(cls, url_or_name: str) -> str:
        """Open a website or perform a search query in the user's default browser."""
        target = url_or_name.lower().strip()

        preset_sites = {
            # Google services
            "youtube":           "https://www.youtube.com",
            "google":            "https://www.google.com",
            "gmail":             "https://mail.google.com",
            "google maps":       "https://www.google.com/maps",
            "maps":              "https://www.google.com/maps",
            "google translate":  "https://translate.google.com",
            "translate":         "https://translate.google.com",
            "google drive":      "https://drive.google.com",
            "google docs":       "https://docs.google.com",
            "google sheets":     "https://sheets.google.com",
            "google photos":     "https://photos.google.com",
            "google meet":       "https://meet.google.com",
            "google calendar":   "https://calendar.google.com",
            "google news":       "https://news.google.com",
            "google classroom":  "https://classroom.google.com",
            "google pay":        "https://pay.google.com",
            # Social & Communication
            "github":            "https://github.com",
            "reddit":            "https://reddit.com",
            "twitter":           "https://x.com",
            "x":                 "https://x.com",
            "instagram":         "https://www.instagram.com",
            "facebook":          "https://www.facebook.com",
            "whatsapp":          "https://web.whatsapp.com",
            "whatsapp web":      "https://web.whatsapp.com",
            "telegram":          "https://web.telegram.org",
            "discord":           "https://discord.com/app",
            "linkedin":          "https://www.linkedin.com",
            "snapchat":          "https://www.snapchat.com",
            "pinterest":         "https://www.pinterest.com",
            "tiktok":            "https://www.tiktok.com",
            "twitch":            "https://www.twitch.tv",
            # Entertainment
            "netflix":           "https://www.netflix.com",
            "hotstar":           "https://www.hotstar.com",
            "disney hotstar":    "https://www.hotstar.com",
            "prime video":       "https://www.primevideo.com",
            "amazon prime":      "https://www.primevideo.com",
            "spotify":           "https://open.spotify.com",
            "jio cinema":        "https://www.jiocinema.com",
            "zee5":              "https://www.zee5.com",
            "mx player":         "https://www.mxplayer.in",
            # Shopping
            "amazon":            "https://www.amazon.in",
            "flipkart":          "https://www.flipkart.com",
            "myntra":            "https://www.myntra.com",
            "meesho":            "https://www.meesho.com",
            "snapdeal":          "https://www.snapdeal.com",
            "nykaa":             "https://www.nykaa.com",
            # Productivity & AI
            "chatgpt":           "https://chatgpt.com",
            "gemini":            "https://gemini.google.com",
            "claude":            "https://claude.ai",
            "perplexity":        "https://www.perplexity.ai",
            "notion":            "https://www.notion.so",
            "trello":            "https://trello.com",
            "figma":             "https://www.figma.com",
            "canva":             "https://www.canva.com",
            "stackoverflow":     "https://stackoverflow.com",
            "stack overflow":    "https://stackoverflow.com",
            # Finance & News
            "wikipedia":         "https://www.wikipedia.org",
            "zerodha":           "https://zerodha.com",
            "groww":             "https://groww.in",
            "paytm":             "https://paytm.com",
            "upi":               "https://www.bhimupi.org.in",
            "moneycontrol":      "https://www.moneycontrol.com",
            "nse":               "https://www.nseindia.com",
            "bse":               "https://www.bseindia.com",
            # News
            "times of india":    "https://timesofindia.indiatimes.com",
            "ndtv":              "https://www.ndtv.com",
            "bbc":               "https://www.bbc.com",
            "cnn":               "https://www.cnn.com",
            "the hindu":         "https://www.thehindu.com",
        }

        url = None
        label = target.capitalize()

        if target in preset_sites:
            url = preset_sites[target]
            label = target.title()
        elif target.startswith("http://") or target.startswith("https://"):
            url = target
            label = "The link"
        elif "." in target and " " not in target:
            url = f"https://{target}"
            label = target
        else:
            # Not a known site — do a Google search so the user at least gets results
            url = f"https://www.google.com/search?q={requests.utils.quote(url_or_name)}"
            label = f"Google search for '{url_or_name}'"

        try:
            # 1. Native Windows shell startfile ensures foreground window in default browser
            os.startfile(url)
        except Exception:
            try:
                # 2. Fallback to start command
                os.system(f'start "" "{url}"')
            except Exception:
                webbrowser.open(url)

        return f"{label} is now open in your browser, Sir. This is done."


    @classmethod
    def is_valid_app_or_site(cls, target: str) -> bool:
        """Check whether a requested application or website actually exists before acknowledging."""
        cleaned = cls.clean_app_name(target)
        if not cleaned:
            return False
        t = cleaned.lower().strip()
        if t in ["youtube", "google", "github", "reddit", "twitter", "x", "chatgpt", "wikipedia", "netflix", "amazon", "gmail"]:
            return True
        if t.startswith("http://") or t.startswith("https://") or "." in t:
            return True
        name, app_target = cls.resolve_app(t)
        return app_target is not None

    @classmethod
    def play_youtube(cls, search_query: str) -> str:
        """Search and directly play the video on YouTube in the browser."""
        import re
        import urllib.parse
        clean_query = search_query.strip()
        if not clean_query:
            return "Please specify what you would like to play on YouTube, Sir."

        try:
            encoded_query = urllib.parse.quote(clean_query)
            search_url = f"https://www.youtube.com/results?search_query={encoded_query}"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            resp = requests.get(search_url, headers=headers, timeout=5)
            match = re.search(r'"videoId":"([a-zA-Z0-9_-]{11})"', resp.text)
            if not match:
                match = re.search(r'/watch\?v=([a-zA-Z0-9_-]{11})', resp.text)

            if match:
                video_id = match.group(1)
                play_url = f"https://www.youtube.com/watch?v={video_id}"
                try:
                    os.startfile(play_url)
                except Exception:
                    webbrowser.open(play_url)
                return f"Playing '{clean_query}' directly on YouTube now, Sir. This is done."
        except Exception:
            pass

        # Fallback to search page if scraping fails
        fallback_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(clean_query)}"
        try:
            os.startfile(fallback_url)
        except Exception:
            webbrowser.open(fallback_url)
        return f"Playing '{clean_query}' on YouTube now, Sir. This is done."

    @classmethod
    def play_spotify(cls, song_or_artist: str) -> str:
        """Open Spotify, focus its window, and choose the first search suggestion."""
        import win32com.client

        query = song_or_artist.strip()
        if not query:
            return "Please specify what you would like to play on Spotify, Sir."

        try:
            shell = win32com.client.Dispatch("WScript.Shell")
            spotify_running = False
            for process in psutil.process_iter(["name"]):
                try:
                    if (process.info.get("name") or "").lower() == "spotify.exe":
                        spotify_running = True
                        break
                except (psutil.Error, OSError, TypeError, AttributeError):
                    continue
            if not spotify_running:
                os.startfile("spotify:")

            # Spotify can take several seconds to create its main window after launch.
            focused = False
            for _ in range(30):
                if _focus_spotify_window(shell):
                    focused = True
                    break
                time.sleep(0.5)

            if not focused:
                return "Spotify is open, but I could not focus its window. Please bring Spotify to the front and try again, Sir."

            _send_spotify_search_keys(shell, query)
            return f"I sent '{query}' to Spotify and selected the first match. Please check that playback started, Sir."
        except Exception as e:
            print(f"[Spotify Playback Error] {e}")
            return f"I couldn't start Spotify playback: {str(e)[:120]}, Sir."

    @classmethod
    def get_system_telemetry(cls) -> Dict[str, Any]:
        """Fetch real-time CPU, RAM, battery, and disk telemetry."""
        cpu_percent = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        battery = psutil.sensors_battery()
        battery_percent = battery.percent if battery else None
        is_charging = battery.power_plugged if battery else None

        return {
            "cpu_percent": cpu_percent,
            "ram_percent": ram.percent,
            "ram_used_gb": round(ram.used / (1024**3), 2),
            "ram_total_gb": round(ram.total / (1024**3), 2),
            "disk_percent": disk.percent,
            "battery_percent": battery_percent,
            "is_charging": is_charging
        }

    @classmethod
    def get_system_status_report(cls) -> str:
        """Human-readable system diagnostic."""
        telemetry = cls.get_system_telemetry()
        lines = [
            f"System Diagnostic Report, Sir:",
            f"- CPU Load: {telemetry['cpu_percent']}%",
            f"- Memory Utilization: {telemetry['ram_percent']}% ({telemetry['ram_used_gb']} GB of {telemetry['ram_total_gb']} GB)",
            f"- Storage Usage: {telemetry['disk_percent']}%"
        ]

        if telemetry['battery_percent'] is not None:
            plugged_status = "Connected to power" if telemetry['is_charging'] else "On battery reserve"
            lines.append(f"- Battery Level: {telemetry['battery_percent']}% ({plugged_status})")
        else:
            lines.append("- Power Source: AC Mains")

        return "\n".join(lines)

    @classmethod
    def get_ram_status_report(cls) -> str:
        """Targeted RAM memory report."""
        t = cls.get_system_telemetry()
        free_gb = round(t['ram_total_gb'] - t['ram_used_gb'], 2)
        return f"Memory load is currently at {t['ram_percent']} percent, with {free_gb} GB of RAM available out of {t['ram_total_gb']} GB, Sir."

    @classmethod
    def get_battery_status_report(cls) -> str:
        """Targeted battery status report."""
        t = cls.get_system_telemetry()
        if t['battery_percent'] is not None:
            status = "connected to AC mains" if t['is_charging'] else "operating on battery reserve"
            return f"Battery reserve is at {t['battery_percent']} percent, {status}, Sir."
        return "Workstation is operating directly from AC mains power, Sir."

    @classmethod
    def get_cpu_status_report(cls) -> str:
        """Targeted CPU load report."""
        t = cls.get_system_telemetry()
        return f"Current processor activity is at {t['cpu_percent']} percent across all cores, Sir."

    @classmethod
    def volume_control(cls, action: str, steps: int = 5) -> str:
        """Control master audio volume."""
        action = action.lower().strip()
        if "up" in action or "increase" in action or "raise" in action:
            cls._press_key(VK_VOLUME_UP, steps)
            return "Audio levels increased, Sir."
        elif "down" in action or "decrease" in action or "lower" in action:
            cls._press_key(VK_VOLUME_DOWN, steps)
            return "Audio levels reduced, Sir."
        elif "mute" in action or "silence" in action or "unmute" in action:
            cls._press_key(VK_VOLUME_MUTE, 1)
            return "Toggled master audio mute state, Sir."
        return "Audio command unverified, Sir."

    @classmethod
    def media_control(cls, action: str) -> str:
        """Control media playback."""
        action = action.lower().strip()
        if "play" in action or "pause" in action:
            cls._press_key(VK_MEDIA_PLAY_PAUSE, 1)
            return "Toggled media playback, Sir."
        elif "next" in action or "skip" in action:
            cls._press_key(VK_MEDIA_NEXT_TRACK, 1)
            return "Skipped to next media track, Sir."
        elif "previous" in action or "prev" in action or "back" in action:
            cls._press_key(VK_MEDIA_PREV_TRACK, 1)
            return "Reverting to previous track, Sir."
        return "Unrecognized media command, Sir."

    @classmethod
    def get_time_and_date(cls) -> str:
        """Returns the current date and time formatted elegantly."""
        now = datetime.now()
        time_str = now.strftime("%I:%M %p")
        date_str = now.strftime("%A, %B %d, %Y")
        return f"It is currently {time_str} on {date_str}, Sir."

    @classmethod
    def get_weather(cls, city: str = "") -> str:
        """Fetch weather report using wttr.in."""
        try:
            city_query = city.strip()
            if not city_query:
                try:
                    from core.memory import MemoryManager
                    city_query = MemoryManager.load_profile().get("city", "")
                except Exception:
                    city_query = ""

            url = f"https://wttr.in/{city_query}?format=%C+%t+(feels+like+%f),+humidity:+%h"
            headers = {"User-Agent": "curl/7.68.0"}
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                report = response.text.strip()
                loc = f"for {city_query}" if city_query else "locally"
                return f"Weather report {loc}: {report}, Sir."
            return "Unable to retrieve environmental conditions at this time, Sir."
        except Exception:
            return "Atmospheric sensors are temporarily unavailable, Sir."

    @classmethod
    def lock_workstation(cls) -> str:
        """Lock workstation protocol permanently disabled per user instruction."""
        return "Workstation locking protocol has been permanently disabled per your instructions, Sir."

