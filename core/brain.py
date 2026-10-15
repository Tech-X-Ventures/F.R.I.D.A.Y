import json
from typing import List, Dict, Any, Tuple
from core.config import Config
from core.system_control import SystemControl
from core.memory import MemoryManager

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

# OpenAI / Groq Tool specifications
JARVIS_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "open_application",
            "description": "Launch a desktop application like Notepad, Chrome, Calculator, VS Code, Task Manager, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {"type": "string", "description": "The name of the application to launch."}
                },
                "required": ["app_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_website",
            "description": "Open a website or search query in the browser (e.g. YouTube, Google, GitHub, or any query).",
            "parameters": {
                "type": "object",
                "properties": {
                    "url_or_name": {"type": "string", "description": "Target website name, link, or search query."}
                },
                "required": ["url_or_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "play_youtube",
            "description": "Search and play a video, song, or topic on YouTube.",
            "parameters": {
                "type": "object",
                "properties": {
                    "search_query": {"type": "string", "description": "Title or topic of video to search."}
                },
                "required": ["search_query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "play_spotify",
            "description": "Search and play music, song, artist, or playlist on Spotify.",
            "parameters": {
                "type": "object",
                "properties": {
                    "search_query": {"type": "string", "description": "Title of song, artist, or track to play on Spotify."}
                },
                "required": ["search_query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_system_status",
            "description": "Retrieve current computer system diagnostics including CPU load, RAM usage, storage, and battery level.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "control_volume",
            "description": "Control system master audio volume (up, down, mute, unmute).",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["up", "down", "mute"], "description": "Audio adjustment action."}
                },
                "required": ["action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_time_and_date",
            "description": "Get current time, day, and calendar date.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Check current weather for a specific city or current location.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name, or empty for local weather."}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "remember_fact",
            "description": "Save important user facts, personal preferences, reminders, or details to permanent memory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fact": {"type": "string", "description": "The exact fact, note, or reminder to remember permanently."}
                },
                "required": ["fact"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_user_profile",
            "description": "Update specific user profile details such as city, birthday, favorite music, or goals.",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Profile field name (e.g. 'city', 'birthday', 'favorites.music_genre', 'goals')"},
                    "value": {"type": "string", "description": "The new value to set"}
                },
                "required": ["key", "value"]
            }
        }
    }
]

class JarvisBrain:
    def __init__(self):
        # Load persistent chat memory from disk
        recent = MemoryManager.load_recent_chats(limit=10)
        self.history: List[Dict[str, Any]] = recent if recent else []
        self._max_history = 12

    def get_system_prompt(self) -> str:
        user_name = Config.get_user_name()
        profile_context = MemoryManager.get_profile_context()
        return (
            f"You are FRYDAY, the sophisticated, witty, "
            f"and impeccably polite AI assistant developed by Prateek Sharma. "
            f"You are speaking with {user_name}. Always address them respectfully as '{user_name}'.\n\n"
            f"{profile_context}\n\n"
            f"Core Creator & Identity Guidelines:\n"
            f"- You were designed and developed by Prateek Sharma. Whenever asked who created you, who made you, "
            f"or who your developer is, always state proudly, politely, and explicitly that you were developed by Prateek Sharma.\n"
            f"Key Personality Guidelines:\n"
            f"1. Tone: Calm, refined British butler elegance, quietly confident, loyal, and subtly humorous.\n"
            f"2. Concurrency & Voice Delivery: Your responses will always be spoken aloud. Keep responses concise, "
            f"crisp, and natural.\n"
            f"3. System Actions & Application Opening: When asked to launch apps, websites, or control the system, "
            f"always explicitly confirm to the user that the application has been opened and the task is done "
            f"(e.g., 'Notepad is now open, {user_name}. This is done.', 'Chrome has been opened for you, {user_name}.').\n"
            f"4. You have full awareness of the physical workstation, hardware telemetry, and your creator's personal profile."
        )

    def _execute_tool(self, tool_name: str, args: Dict[str, Any]) -> str:
        """Execute a local system tool and return status string."""
        try:
            if tool_name == "open_application":
                return SystemControl.open_application(args.get("app_name", ""))
            elif tool_name == "open_website":
                return SystemControl.open_website(args.get("url_or_name", ""))
            elif tool_name == "play_youtube":
                return SystemControl.play_youtube(args.get("search_query", ""))
            elif tool_name == "play_spotify":
                return SystemControl.play_spotify(args.get("search_query", ""))
            elif tool_name == "get_system_status":
                return SystemControl.get_system_status_report()
            elif tool_name == "control_volume":
                return SystemControl.volume_control(args.get("action", "up"))
            elif tool_name == "get_time_and_date":
                return SystemControl.get_time_and_date()
            elif tool_name == "get_weather":
                return SystemControl.get_weather(args.get("city", ""))
            elif tool_name == "remember_fact":
                return MemoryManager.add_custom_memory(args.get("fact", ""))
            elif tool_name == "update_user_profile":
                return MemoryManager.update_profile_field(args.get("key", ""), args.get("value", ""))
            elif tool_name == "lock_workstation":
                return SystemControl.lock_workstation()
            return f"Action '{tool_name}' completed."
        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"

    def _add_to_history(self, role: str, content: str):
        """Append to conversation history, maintain strictly bounded context window, and persist to disk."""
        self.history.append({"role": role, "content": content})
        max_entries = self._max_history * 2
        if len(self.history) > max_entries:
            self.history = self.history[-max_entries:]
        # Persist to disk
        try:
            MemoryManager.save_chat_turn(role, content)
        except Exception:
            pass

    def _check_fast_intent(self, text: str) -> Tuple[bool, str]:
        """
        Check for direct system intents to provide instant zero-latency responses
        even if API key is not configured or offline.
        """
        t = text.lower().strip()

        # Creator / Developer queries
        if any(k in t for k in [
            "who created you", "who made you", "who is your creator", "who developed you",
            "who is your developer", "who programmed you", "who built you", "who designed you",
            "who wrote your code", "who is your master", "who made fryday", "who made jarvis"
        ]):
            return True, f"I was designed and developed by Prateek Sharma, {Config.get_user_name()}."

        # Tony Stark queries
        if any(k in t for k in ["where is mr. stark", "where is mr stark", "where is tony stark", "where is tony"]):
            return True, f"Mr. Stark is currently off-grid, {Config.get_user_name()}. However, I am fully operational under the design of my developer, Prateek Sharma."

        # Memory / Recording Commands
        if t.startswith("remember that "):
            fact = text.strip()[len("remember that "):].strip()
            return True, MemoryManager.add_custom_memory(fact)
        if t.startswith("remember "):
            fact = text.strip()[len("remember "):].strip()
            return True, MemoryManager.add_custom_memory(fact)
        if t.startswith("note that "):
            fact = text.strip()[len("note that "):].strip()
            return True, MemoryManager.add_custom_memory(fact)

        # Creator / User Identity & Profile Retrieval
        if any(k in t for k in [
            "who am i", "what do you know about me", "tell me about myself",
            "what are my memories", "what do you remember about me", "my profile"
        ]):
            p = MemoryManager.load_profile()
            name = p.get("name", "Prateek Sharma")
            role = p.get("role", "Developer")
            city = p.get("city", "Delhi")
            tech = ", ".join(p.get("tech_stack", []))
            custom = p.get("custom_memories", [])
            mem_text = "\n".join([f"- {m}" for m in custom]) if custom else "- None recorded yet."
            return True, (
                f"You are {name}, my developer and architect, Sir.\n"
                f"- Base Location: {city}\n"
                f"- Specialization: {tech}\n"
                f"- Primary Role: {role}\n"
                f"Permanent Memories on record:\n{mem_text}"
            )

        # Chat History Reset
        if any(k in t for k in ["clear chat history", "clear chat memory", "reset chat history", "forget our conversation"]):
            self.history = []
            return True, MemoryManager.clear_chat_history()

        # Favorite Music Shortcut
        if any(k in t for k in ["play my favorite music", "play my favorite songs", "play my favorite song", "play favorite music"]):
            p = MemoryManager.load_profile()
            fav_music = p.get("favorites", {}).get("favorite_artists", "Queen")
            return True, SystemControl.play_youtube(fav_music)

        # Degenerate commands
        if t in ["open", "launch"]:
            return True, "Please specify an application or website you would like me to open, Sir."
        if t in ["weather in", "weather of"]:
            return True, "Please specify a city for the atmospheric report, Sir."
        if t in ["play on youtube", "play youtube"]:
            return True, "Please specify what you would like to search or play on YouTube, Sir."

        # Specific Targeted Telemetry
        if any(k in t for k in ["how much ram", "ram left", "ram usage", "memory left", "memory usage", "check ram", "check my ram"]):
            return True, SystemControl.get_ram_status_report()

        if any(k in t for k in ["battery level", "battery percentage", "check battery", "battery status", "how much battery", "battery"]):
            return True, SystemControl.get_battery_status_report()

        if any(k in t for k in ["cpu load", "cpu usage", "processor load", "processor usage", "check cpu", "cpu"]):
            return True, SystemControl.get_cpu_status_report()

        # General System status / health
        if any(k in t for k in [
            "system status", "diagnostics", "diagnostic", "system health", "pc health", "workstation status"
        ]):
            return True, SystemControl.get_system_status_report()

        # Time and date
        if any(k in t for k in [
            "what time is it", "tell me the time", "current time", "what's the time",
            "what date is today", "what's the date", "what is today's date", "what day is today", "current date"
        ]):
            return True, SystemControl.get_time_and_date()

        # Audio volume controls
        if any(k in t for k in ["volume up", "increase volume", "raise volume", "turn up the volume", "louder", "crank the volume"]):
            return True, SystemControl.volume_control("up")
        if any(k in t for k in ["volume down", "decrease volume", "lower volume", "turn down the volume", "softer", "quieter"]):
            return True, SystemControl.volume_control("down")
        if any(k in t for k in ["mute", "silence", "unmute", "shut up", "be quiet"]):
            return True, SystemControl.volume_control("mute")

        # Lock PC / Workstation
        if any(k in t for k in ["lock pc", "lock computer", "lock workstation", "lock the screen"]):
            return True, SystemControl.lock_workstation()

        # Open applications & software
        for prefix in ["fryday open ", "fryday launch ", "fryday please open ", "jarvis open ", "jarvis launch ", "jarvis please open ", "please open ", "please launch ", "open ", "launch ", "start "]:
            if t.startswith(prefix):
                raw_target = t[len(prefix):].strip()
                clean_target = SystemControl.clean_app_name(raw_target)
                if not clean_target:
                    return True, "Which application would you like me to open, Sir?"

                # Handle pronoun references ("open that", "open it", "launch this")
                if clean_target.lower() in ["that", "it", "this", "the app", "the application", "same"]:
                    recent_app = None
                    for turn in reversed(self.history[-4:]):
                        c = turn.get("content", "").lower()
                        for candidate in ["linkedin", "linkdin", "chrome", "notepad", "youtube", "calculator", "calc", "spotify", "vscode", "vs code", "code", "whatsapp", "word", "excel", "powerpoint", "terminal"]:
                            if candidate in c:
                                recent_app = candidate
                                break
                        if recent_app:
                            break
                    if recent_app:
                        clean_target = recent_app
                    else:
                        return False, ""

                # Detect "open <website> on chrome/browser/edge/firefox" pattern
                # e.g. "open google maps on chrome" → open google maps website
                browser_suffixes = [
                    " on chrome", " on google chrome", " on browser", " in chrome",
                    " in browser", " in google chrome", " on edge", " in edge",
                    " on firefox", " in firefox", " on microsoft edge"
                ]
                website_target = clean_target.lower()
                matched_suffix = None
                for suffix in browser_suffixes:
                    if website_target.endswith(suffix):
                        website_target = website_target[:-len(suffix)].strip()
                        matched_suffix = suffix
                        break

                if matched_suffix:
                    # User said "open X on chrome/browser" — treat X as a website/search
                    return True, SystemControl.open_website(website_target)

                # Check against every key in open_website's preset_sites dict (exact match)
                # This prevents "google translate" / "google drive" / "google docs" etc.
                # from fuzzy-matching to Chrome just because they contain the word "google"
                known_websites = {
                    # Google services
                    "youtube", "google", "gmail", "google maps", "maps",
                    "google translate", "translate", "google drive", "drive",
                    "google docs", "docs", "google sheets", "sheets",
                    "google photos", "photos", "google meet", "meet",
                    "google calendar", "calendar", "google news", "news",
                    "google classroom", "classroom", "google pay", "pay",
                    # Social & Communication
                    "github", "reddit", "twitter", "x", "instagram", "facebook",
                    "whatsapp", "whatsapp web", "telegram", "discord", "linkedin",
                    "snapchat", "pinterest", "tiktok", "twitch",
                    # Entertainment
                    "netflix", "hotstar", "disney hotstar", "prime video",
                    "amazon prime", "spotify", "jio cinema", "zee5", "mx player",
                    # Shopping
                    "amazon", "flipkart", "myntra", "meesho", "snapdeal", "nykaa",
                    # Productivity & AI
                    "chatgpt", "gemini", "claude", "perplexity", "notion",
                    "trello", "figma", "canva", "stackoverflow", "stack overflow",
                    # Finance & News
                    "wikipedia", "zerodha", "groww", "paytm", "upi",
                    "moneycontrol", "nse", "bse", "times of india", "ndtv",
                    "bbc", "cnn", "the hindu",
                }
                # Some names exist as both desktop apps AND websites.
                # If the user just says "open spotify" (no browser suffix), prefer desktop app.
                prefer_desktop_app = {
                    "spotify", "discord", "whatsapp", "telegram", "steam",
                }
                if clean_target.lower() in prefer_desktop_app:
                    return True, SystemControl.open_application(clean_target)

                if clean_target.lower() in known_websites or "." in clean_target:
                    return True, SystemControl.open_website(clean_target)
                return True, SystemControl.open_application(clean_target)




        # Media Playback (YouTube & Spotify)
        norm_play = t
        for prefix in ["fryday please play ", "please play ", "fryday play ", "jarvis please play ", "jarvis play ", "play "]:
            if norm_play.startswith(prefix):
                content = norm_play[len(prefix):].strip()
                # Check if it specifies Spotify
                if "on spotify" in content:
                    query = content.replace("on spotify", "").strip()
                    for word in ["song", "track", "music"]:
                        if query.endswith(" " + word):
                            query = query[:-len(word)-1].strip()
                    return True, SystemControl.play_spotify(query)

                # Check if it specifies YouTube
                if "on youtube" in content:
                    query = content.replace("on youtube", "").strip()
                    for word in ["song", "track", "video"]:
                        if query.endswith(" " + word):
                            query = query[:-len(word)-1].strip()
                    return True, SystemControl.play_youtube(query)

                # Default to YouTube playback if query contains song/music or general title
                query = content
                for word in ["song on youtube", "on youtube", "song"]:
                    if query.endswith(" " + word):
                        query = query[:-len(word)-1].strip()
                return True, SystemControl.play_youtube(query)

        # Compound command: "open youtube and play <song>"
        if "open youtube and play " in t or "youtube and play " in t:
            if "open youtube and play " in t:
                query = t.split("open youtube and play ", 1)[1].strip()
            else:
                query = t.split("youtube and play ", 1)[1].strip()
            return True, SystemControl.play_youtube(query)

        # Weather
        if "weather in " in t:
            city = t.split("weather in ", 1)[1].strip("? .")
            if not city:
                return True, "Please specify a city for the atmospheric report, Sir."
            return True, SystemControl.get_weather(city)
        if t in ["weather", "what is the weather", "how is the weather", "weather report"]:
            return True, SystemControl.get_weather()

        return False, ""

    def process_query(self, user_query: str) -> str:
        """
        Process user query through Fast-Intent matcher or LLM Brain (Groq / OpenAI).
        """
        query_clean = user_query.strip()
        if not query_clean:
            return "At your service, Sir."

        # 1. Check instant local commands
        is_fast, fast_response = self._check_fast_intent(query_clean)
        if is_fast:
            self._add_to_history("user", query_clean)
            self._add_to_history("assistant", fast_response)
            return fast_response

        # 2. Check API Key
        api_key = Config.get_api_key()
        provider = Config.get_provider()
        model_name = Config.get_model()

        if not api_key:
            return (
                f"I am standing by, {Config.get_user_name()}. My local system controls are active, "
                f"but to enable conversational intelligence, please enter your Groq or OpenAI API key "
                f"in the Settings panel (gear icon at the top right)."
            )

        # 3. Initialize OpenAI/Groq Client
        base_url = "https://api.groq.com/openai/v1" if provider == "groq" else None

        try:
            client = OpenAI(api_key=api_key, base_url=base_url)
            
            # Prepare message chain
            messages = [{"role": "system", "content": self.get_system_prompt()}]
            # Add recent history
            messages.extend(self.history[-self._max_history:])
            # Add new user message
            messages.append({"role": "user", "content": query_clean})

            # Call LLM with tool calling
            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                tools=JARVIS_TOOLS,
                tool_choice="auto",
                temperature=0.7,
                max_tokens=600
            )

            msg = response.choices[0].message

            # Handle Tool Calls
            if msg.tool_calls:
                # Append assistant tool call message
                messages.append(msg)

                for tool_call in msg.tool_calls:
                    fn_name = tool_call.function.name
                    try:
                        fn_args = json.loads(tool_call.function.arguments)
                    except Exception:
                        fn_args = {}

                    tool_result = self._execute_tool(fn_name, fn_args)

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_result
                    })

                # Follow-up completion to provide suave spoken response after tool action
                followup = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=400
                )
                final_text = followup.choices[0].message.content or "Task completed, Sir."
            else:
                final_text = msg.content or "Understood, Sir."

            # Update memory
            self._add_to_history("user", query_clean)
            self._add_to_history("assistant", final_text)

            return final_text

        except Exception as e:
            err_msg = str(e)
            print(f"[Brain Error] {err_msg}")
            if "AuthenticationError" in err_msg or "401" in err_msg:
                return f"Authentication failed, Sir. Please check your {provider.capitalize()} API key in settings."
            return f"I encountered an anomaly in my neural subroutines: {err_msg[:120]}, Sir."
