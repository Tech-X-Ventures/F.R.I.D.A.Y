import time
import threading
import tkinter as tk
import customtkinter as ctk
from datetime import datetime
from typing import Optional
import os
import ctypes

from core.config import Config
from core.voice_engine import VoiceEngine
from core.brain import JarvisBrain
from core.system_control import SystemControl
from gui.arc_reactor import ArcReactorCanvas
from gui.settings_dialog import SettingsDialog

# ── Taskbar: tell Windows this is FRYDAY, not pythonw.exe ──────────────────
try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Prateek.FRYDAY.Assistant.1")
except Exception:
    pass

# Set CustomTkinter theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class JarvisApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window Configuration
        self.title("FRYDAY  //  ADVANCED TACTICAL INTERFACE")
        self.geometry("1100x720")
        self.minsize(980, 640)
        self.configure(fg_color="#070c16")

        # Set window & taskbar icon (deferred — CustomTkinter needs window drawn first)
        import os as _os
        self._ico_path = _os.path.join(_os.path.dirname(_os.path.dirname(__file__)), "fryday.ico")
        self.after(100, self._apply_icon)

        # Initialize Brain and Voice Engine
        self.brain = JarvisBrain()
        self.voice = VoiceEngine(on_state_change=self._on_voice_state_change)

        self._current_state = "IDLE"
        self._running = True
        self.voice_listening_enabled = True  # Always in voice ON mode after opening!
        self._cancel_active_query = False

        self._build_ui()
        self._start_telemetry_loop()

        # Handle clean window closing
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Hotkey for emergency vocal interruption (Escape key)
        self.bind("<Escape>", lambda e: self._on_stop_speech_hotkey())

        # Ask for an API key on startup only when AI is not configured.
        self.after(1000, self._check_first_run_setup)

    def _check_first_run_setup(self):
        if Config.get_api_key():
            self._initial_greeting()
            return

        from gui.api_key_setup import APIKeySetupDialog

        APIKeySetupDialog(
            self,
            on_complete=lambda: self.after(0, self._initial_greeting),
        )

    def _apply_icon(self):
        """Apply FRYDAY .ico to title bar AND Windows taskbar."""
        try:
            self.iconbitmap(self._ico_path)
            self.wm_iconbitmap(self._ico_path)
        except Exception:
            pass
        # Call again at 500ms — ensures taskbar refreshes after window is fully visible
        self.after(500, self._apply_icon_final)

    def _apply_icon_final(self):
        """Second pass — locks icon into taskbar."""
        try:
            self.iconbitmap(self._ico_path)
            self.wm_iconbitmap(self._ico_path)
        except Exception:
            pass

    def _initial_greeting(self):
        """
        Iron Man 'Daddy's Home' style boot sequence.
        Show the boot overlay, then greet the user without reading saved memories aloud.
        """
        from gui.boot_sequence import BootSequenceOverlay

        # Hide main window during boot overlay
        self.withdraw()

        def on_boot_complete():
            """Called when the boot animation finishes."""
            self.deiconify()
            self.lift()
            self.after(300, self._deliver_greeting)

        BootSequenceOverlay(self, on_complete=on_boot_complete)

    def _deliver_greeting(self):
        """
        Greet the user after boot. Personal memories are not pending tasks and must
        never be announced automatically at startup.
        Runs in a background thread so voice/sleep don't block the UI.
        """
        def _run():
            from datetime import datetime

            now      = datetime.now()
            hour     = now.hour
            minute   = now.strftime("%M")
            day_name = now.strftime("%A")
            date_str = now.strftime("%d %B %Y")

            if 5 <= hour < 12:
                period = "Good morning"
            elif 12 <= hour < 17:
                period = "Good afternoon"
            else:
                period = "Good evening"

            user_name = Config.get_user_name()

            # ── Opening line ──────────────────────────────────────────────────
            opening = (
                f"{period}, {user_name}. "
                f"All systems are online. "
                f"Today is {day_name}, {date_str}. "
                f"The time is {hour} {minute}."
            )
            self.after(0, lambda: self._add_message("FRYDAY", f"⚡ {opening}"))
            self.voice.speak(opening)

            # ── Sign-off ──────────────────────────────────────────────────────
            signoff = "Voice interface is hot. Standing by for your command."
            self.after(0, lambda: self._add_message("FRYDAY", f"🎙️ {signoff}"))
            self.voice.speak(signoff)

            # Start continuous listener after the greeting finishes
            self.after(500, self._start_continuous_listener)

        threading.Thread(target=_run, daemon=True).start()


    def _on_close(self):
        self._running = False
        self.voice_listening_enabled = False
        self.voice.stop_listening()
        self.destroy()

    def _build_ui(self):
        # 1. TOP HEADER BAR
        top_bar = ctk.CTkFrame(self, fg_color="#0d1524", height=60, corner_radius=0)
        top_bar.pack(fill="x", side="top")

        # Logo and Title
        lbl_title = ctk.CTkLabel(
            top_bar, text="FRYDAY",
            font=ctk.CTkFont(family="Consolas", size=22, weight="bold"),
            text_color="#00e5ff"
        )
        lbl_title.pack(side="left", padx=(25, 10))

        lbl_subtitle = ctk.CTkLabel(
            top_bar, text="// DEVELOPED BY PRATEEK SHARMA",
            font=ctk.CTkFont(family="Consolas", size=12),
            text_color="#4f759b"
        )
        lbl_subtitle.pack(side="left", padx=(0, 20))

        # Real-time Telemetry Status Strip
        self.lbl_telemetry = ctk.CTkLabel(
            top_bar, text="CPU: --% | RAM: --% | PWR: --",
            font=ctk.CTkFont(family="Consolas", size=12),
            text_color="#00ffc4"
        )
        self.lbl_telemetry.pack(side="left", padx=20)

        # Settings Button
        btn_settings = ctk.CTkButton(
            top_bar, text="⚙ CONFIG", width=100, height=32,
            fg_color="#13243a", hover_color="#1d3759", text_color="#00e5ff",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            command=self._open_settings
        )
        btn_settings.pack(side="right", padx=(10, 25))

        # Status Pill Badge
        self.status_badge = ctk.CTkLabel(
            top_bar, text="● ONLINE",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            text_color="#00ff88"
        )
        self.status_badge.pack(side="right", padx=15)

        # 2. MAIN SPLIT BODY
        body_frame = ctk.CTkFrame(self, fg_color="transparent")
        body_frame.pack(fill="both", expand=True, padx=20, pady=15)

        # -----------------------------
        # LEFT PANEL: ARC REACTOR & HUD
        # -----------------------------
        left_panel = ctk.CTkFrame(
            body_frame, fg_color="#0b1322", corner_radius=16,
            border_width=1, border_color="#172740", width=380
        )
        left_panel.pack(side="left", fill="y", padx=(0, 15))
        left_panel.pack_propagate(False)

        # Arc Reactor Canvas
        self.arc_reactor = ArcReactorCanvas(left_panel, size=240, bg_color="#0b1322")
        self.arc_reactor.pack(pady=(25, 10))

        # Core Status Label
        self.lbl_hud_status = ctk.CTkLabel(
            left_panel, text="CORE: STANDBY",
            font=ctk.CTkFont(family="Consolas", size=16, weight="bold"),
            text_color="#00e5ff"
        )
        self.lbl_hud_status.pack(pady=(0, 15))

        # Big Voice Activation Button (Always-On Voice Toggle)
        self.btn_mic = ctk.CTkButton(
            left_panel, text="🎙  VOICE ON: LISTENING", height=48,
            fg_color="#007acc", hover_color="#0090db",
            font=ctk.CTkFont(family="Consolas", size=13, weight="bold"),
            corner_radius=24,
            command=self._toggle_voice_capture
        )
        self.btn_mic.pack(fill="x", padx=30, pady=(5, 15))

        # Quick Control Panel
        quick_lbl = ctk.CTkLabel(
            left_panel, text="RAPID PROTOCOLS",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            text_color="#4f759b"
        )
        quick_lbl.pack(anchor="w", padx=30, pady=(10, 5))

        quick_grid = ctk.CTkFrame(left_panel, fg_color="transparent")
        quick_grid.pack(fill="x", padx=25, pady=0)

        ctk.CTkButton(
            quick_grid, text="📊 Diagnostics", height=32,
            fg_color="#101d30", hover_color="#1a2e4c", text_color="#a0c0e0",
            command=lambda: self._trigger_quick_cmd("system status")
        ).grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        ctk.CTkButton(
            quick_grid, text="🌐 Browser", height=32,
            fg_color="#101d30", hover_color="#1a2e4c", text_color="#a0c0e0",
            command=lambda: self._trigger_quick_cmd("open google")
        ).grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ctk.CTkButton(
            quick_grid, text="🔊 Vol Up", height=32,
            fg_color="#101d30", hover_color="#1a2e4c", text_color="#a0c0e0",
            command=lambda: self._trigger_quick_cmd("volume up")
        ).grid(row=1, column=0, padx=5, pady=5, sticky="ew")

        ctk.CTkButton(
            quick_grid, text="🔉 Vol Down", height=32,
            fg_color="#101d30", hover_color="#1a2e4c", text_color="#a0c0e0",
            command=lambda: self._trigger_quick_cmd("volume down")
        ).grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        ctk.CTkButton(
            quick_grid, text="🌤️ Weather", height=32,
            fg_color="#101d30", hover_color="#1a2e4c", text_color="#a0c0e0",
            command=lambda: self._trigger_quick_cmd("weather")
        ).grid(row=2, column=0, padx=5, pady=5, sticky="ew")

        ctk.CTkButton(
            quick_grid, text="🕒 Time & Date", height=32,
            fg_color="#101d30", hover_color="#1a2e4c", text_color="#a0c0e0",
            command=lambda: self._trigger_quick_cmd("what time is it")
        ).grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        quick_grid.grid_columnconfigure(0, weight=1)
        quick_grid.grid_columnconfigure(1, weight=1)

        # --------------------------------
        # RIGHT PANEL: CONSOLE TRANSCRIPT
        # --------------------------------
        right_panel = ctk.CTkFrame(
            body_frame, fg_color="#0b1322", corner_radius=16,
            border_width=1, border_color="#172740"
        )
        right_panel.pack(side="right", fill="both", expand=True)

        # Transcript Header
        trans_header = ctk.CTkFrame(right_panel, fg_color="#0e182a", height=38, corner_radius=8)
        trans_header.pack(fill="x", padx=12, pady=(12, 5))

        lbl_trans = ctk.CTkLabel(
            trans_header, text="TERMINAL TELEMETRY & CONVERSATION",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            text_color="#7096be"
        )
        lbl_trans.pack(side="left", padx=15)

        # Scrollable Chat Log
        self.chat_box = ctk.CTkTextbox(
            right_panel, fg_color="#070d18", text_color="#d0e2f5",
            font=ctk.CTkFont(family="Consolas", size=13),
            wrap="word", border_width=1, border_color="#15243b"
        )
        self.chat_box.pack(fill="both", expand=True, padx=12, pady=5)
        self.chat_box.configure(state="disabled")

        # Bottom Input Area
        input_container = ctk.CTkFrame(right_panel, fg_color="transparent")
        input_container.pack(fill="x", padx=12, pady=(5, 12))

        self.entry_cmd = ctk.CTkEntry(
            input_container, height=44,
            placeholder_text="Enter command or question (e.g. 'open youtube', 'diagnostics')...",
            fg_color="#070d18", border_color="#1b3252",
            font=ctk.CTkFont(family="Consolas", size=13)
        )
        self.entry_cmd.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entry_cmd.bind("<Return>", lambda e: self._on_send_click())

        btn_send = ctk.CTkButton(
            input_container, text="SEND ➤", width=95, height=44,
            fg_color="#00a8ff", hover_color="#0090db", text_color="#000000",
            font=ctk.CTkFont(family="Consolas", size=13, weight="bold"),
            command=self._on_send_click
        )
        btn_send.pack(side="right")

    # ==============================
    # TELEMETRY & SYSTEM LOOP
    # ==============================
    def _start_telemetry_loop(self):
        """Periodically update the top telemetry strip."""
        def update_telemetry():
            try:
                tel = SystemControl.get_system_telemetry()
                pwr = f"BAT {tel['battery_percent']}%" if tel['battery_percent'] is not None else "PWR AC"
                text = f"CPU: {tel['cpu_percent']}%  |  RAM: {tel['ram_percent']}% ({tel['ram_used_gb']}G)  |  {pwr}"
                self.after(0, lambda: self.lbl_telemetry.configure(text=text))
            except Exception:
                pass
            self.after(3000, update_telemetry)

        threading.Thread(target=update_telemetry, daemon=True).start()

    # ==============================
    # CONSOLE MESSAGING
    # ==============================
    def _add_message(self, sender: str, message: str):
        """Append a message to the transcript box."""
        now = datetime.now().strftime("%H:%M:%S")
        self.chat_box.configure(state="normal")

        if sender.upper() in ("FRYDAY", "JARVIS"):
            prefix = f"[{now}]  FRYDAY:\n"
        else:
            prefix = f"\n[{now}]  {Config.get_user_name().upper()}:\n"

        self.chat_box.insert("end", prefix + f"{message}\n\n")
        self.chat_box.see("end")
        self.chat_box.configure(state="disabled")

    # ==============================
    # QUERY HANDLING & EXECUTION
    # ==============================
    def _on_send_click(self):
        user_input = self.entry_cmd.get().strip()
        if not user_input:
            return
        self.entry_cmd.delete(0, "end")
        self._dispatch_query(user_input)

    def _trigger_quick_cmd(self, cmd: str):
        self._dispatch_query(cmd)

    def _get_acknowledgment(self, query: str) -> str:
        """Generate immediate natural vocalization to speak while command is executing."""
        q = query.lower().strip()
        user_name = Config.get_user_name()

        # Incomplete / degenerate prompts
        if q in ["open", "launch", "weather in", "play on youtube"]:
            return f"Standing by, {user_name}."

        for prefix in ["fryday open ", "fryday launch ", "fryday please open ", "jarvis open ", "jarvis launch ", "jarvis please open ", "please open ", "please launch ", "open ", "launch ", "start "]:
            if q.startswith(prefix):
                raw_target = q[len(prefix):].strip()
                clean_target = SystemControl.clean_app_name(raw_target)
                display_name, _ = SystemControl.resolve_app(clean_target)
                app_label = display_name if display_name else clean_target.title()
                if SystemControl.is_valid_app_or_site(clean_target):
                    return f"Opening {app_label} for you now, {user_name}."
                return f"Checking your system for {app_label}, {user_name}."

        if any(k in q for k in ["how much ram", "ram left", "ram usage", "memory usage", "check ram"]):
            return f"Checking memory allocation now, {user_name}."
        elif any(k in q for k in ["battery level", "battery percentage", "check battery", "battery"]):
            return f"Checking battery telemetry now, {user_name}."
        elif any(k in q for k in ["cpu load", "cpu usage", "check cpu"]):
            return f"Checking processor load now, {user_name}."
        elif any(k in q for k in ["diagnostic", "status", "system health", "pc health"]):
            return f"Accessing system diagnostics now, {user_name}."
        elif "volume" in q or "mute" in q or "unmute" in q or "louder" in q or "quieter" in q:
            return f"Adjusting audio levels, {user_name}."
        elif "lock" in q and ("pc" in q or "workstation" in q or "computer" in q or "screen" in q):
            return f"Workstation locking is disabled, {user_name}."
        elif "weather" in q:
            return f"Checking current weather conditions, {user_name}."
        elif "time" in q or "date" in q:
            return f"Checking the current time, {user_name}."
        elif "spotify" in q and ("play" in q or "open" in q):
            return f"Accessing Spotify for playback, {user_name}."
        elif "play" in q and "youtube" in q:
            return f"Searching YouTube for playback, {user_name}."
        elif "and play" in q:
            return f"Searching and initiating playback now, {user_name}."
        elif q.startswith("play ") or "play " in q:
            return f"Queuing media for you, {user_name}."
        elif q.startswith("remember") or q.startswith("note that"):
            return f"Recording that in permanent memory, {user_name}."
        elif any(k in q for k in ["who am i", "what do you know about me", "my profile", "what are my memories"]):
            return f"Accessing user memory core now, {user_name}."
        elif any(k in q for k in ["hello", "hi", "hey", "fryday", "jarvis"]):
            return f"At your service, {user_name}."
        elif any(k in q for k in ["who created you", "who made you", "who developed you"]):
            return f"At your service, {user_name}."
        else:
            return f"Right away, {user_name}."

    def _on_stop_speech_hotkey(self):
        """Immediately interrupt vocal playback and cancel active query on user hotkey."""
        self._cancel_active_query = True
        self.voice.stop_speech()
        self.voice.stop_listening()
        self._set_state("IDLE")
        self._add_message("SYSTEM", "[Playback interrupted by user]")

    def _dispatch_query(self, query: str):
        """Send query to the brain in a background worker, speaking both while executing and after execution."""
        q_clean = query.strip()
        if not q_clean:
            return

        # Check for immediate interrupt / stop commands
        if q_clean.lower() in ["stop", "quiet", "be quiet", "shut up", "cancel", "pause speech"]:
            self._cancel_active_query = True
            self.voice.stop_speech()
            self.voice.stop_listening()
            self._set_state("IDLE")
            self._add_message(Config.get_user_name(), q_clean)
            self._add_message("FRYDAY", "Standing by, Sir.")
            return

        self._cancel_active_query = False
        self._add_message(Config.get_user_name(), q_clean)
        self._set_state("ANALYZING")

        # 1. IMMEDIATE VOCAL ACKNOWLEDGMENT (Speaking while executing)
        ack_phrase = self._get_acknowledgment(q_clean)
        self.voice.speak(ack_phrase)

        def worker():
            # 2. EXECUTE COMMAND OR QUERY
            reply = self.brain.process_query(q_clean)
            if self._cancel_active_query:
                return

            self.after(0, lambda: self._add_message("FRYDAY", reply))

            # 3. FINAL VOCAL RESPONSE (Speaking after executing)
            if not self._cancel_active_query:
                self.voice.speak(reply)

        threading.Thread(target=worker, daemon=True).start()

    # ==============================
    # CONTINUOUS VOICE LISTENER (ALWAYS ON)
    # ==============================
    def _start_continuous_listener(self):
        """Start hands-free background listener thread."""
        threading.Thread(target=self._continuous_listen_loop, daemon=True).start()

    def _continuous_listen_loop(self):
        """Continuous background listener that runs hands-free."""
        # Initial sleep to ensure welcome speech completes smoothly
        time.sleep(2.0)
        last_lvl_time = [0.0]

        while self._running:
            if not self.voice_listening_enabled:
                time.sleep(0.3)
                continue

            # If FRYDAY is currently speaking or queued to speak, wait until finished
            if self.voice.is_speaking or not self.voice.tts_queue.empty():
                time.sleep(0.25)
                continue

            # Brief settle pause to prevent catching speaker room echoes
            time.sleep(0.35)

            if not self.voice_listening_enabled or not self._running:
                continue

            # Audio level callback for arc reactor pulse (rate-limited for smooth 60fps GUI)
            def on_level(lvl):
                now = time.time()
                if now - last_lvl_time[0] >= 0.06:
                    last_lvl_time[0] = now
                    if not self.voice.is_speaking and self.voice_listening_enabled:
                        self.after(0, lambda: self.arc_reactor.set_audio_level(lvl))

            # Record a chunk (up to 4.5 seconds, auto-stops earlier on speech silence)
            transcript = self.voice.record_and_transcribe(
                max_seconds=4.5,
                on_audio_level=on_level
            )

            self.after(0, lambda: self.arc_reactor.set_audio_level(0.0))

            if transcript and transcript.strip():
                clean_t = transcript.strip()
                # Dispatch query on the main UI thread
                self.after(0, lambda t=clean_t: self._dispatch_query(t))
                # Pause loop while query kicks off
                time.sleep(1.2)

    def _toggle_voice_capture(self):
        """Toggle continuous voice listening on/off."""
        if self.voice_listening_enabled:
            # Pause listening
            self.voice_listening_enabled = False
            self.voice.stop_listening()
            self.btn_mic.configure(
                text="🔇  VOICE PAUSED (CLICK TO ACTIVATE)",
                fg_color="#37474f", hover_color="#455a64"
            )
            self._set_state("IDLE")
            self.lbl_hud_status.configure(text="VOICE: PAUSED", text_color="#90a4ae")
        else:
            # Activate listening
            self.voice_listening_enabled = True
            self.btn_mic.configure(
                text="🎙  VOICE ON: LISTENING",
                fg_color="#007acc", hover_color="#0090db"
            )
            self.lbl_hud_status.configure(text="AUDIO: LISTENING...", text_color="#00ffd5")

    # ==============================
    # STATE FEEDBACK & VISUALS
    # ==============================
    def _on_voice_state_change(self, state: str):
        self.after(0, lambda: self._set_state(state))

    def _set_state(self, state: str):
        self._current_state = state
        self.arc_reactor.set_state(state)

        if state == "LISTENING":
            self.lbl_hud_status.configure(text="AUDIO: LISTENING...", text_color="#00ffd5")
            self.status_badge.configure(text="● RECORDING", text_color="#00ffd5")
        elif state == "ANALYZING":
            self.lbl_hud_status.configure(text="NEURAL: PROCESSING...", text_color="#00a8ff")
            self.status_badge.configure(text="● ANALYZING", text_color="#00a8ff")
        elif state == "SPEAKING":
            self.lbl_hud_status.configure(text="VOICE: SYNTHESIZING...", text_color="#38ef7d")
            self.status_badge.configure(text="● VOCALIZING", text_color="#38ef7d")
        else:
            self.lbl_hud_status.configure(text="CORE: STANDBY", text_color="#00e5ff")
            self.status_badge.configure(text="● ONLINE", text_color="#00ff88")

    # ==============================
    # SETTINGS MODAL
    # ==============================
    def _open_settings(self):
        SettingsDialog(
            self,
            on_save_callback=self._on_settings_saved,
            on_test_voice=lambda txt: self.voice.speak(txt)
        )

    def _on_settings_saved(self):
        self._add_message("FRYDAY", "System configuration parameters reloaded and applied, Sir.")
