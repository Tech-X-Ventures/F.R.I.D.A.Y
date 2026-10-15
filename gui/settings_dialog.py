import customtkinter as ctk
from core.config import Config

class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, parent, on_save_callback=None, on_test_voice=None):
        super().__init__(parent)
        self.title("FRYDAY // System Configuration")
        self.geometry("540x620")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.on_save_callback = on_save_callback
        self.on_test_voice = on_test_voice

        # Colors
        self.configure(fg_color="#0b111e")

        self._build_ui()

    def _build_ui(self):
        # Header
        header = ctk.CTkLabel(
            self, text="CORE PARAMETERS & NEURAL LINK",
            font=ctk.CTkFont(family="Consolas", size=18, weight="bold"),
            text_color="#00e5ff"
        )
        header.pack(pady=(20, 15))

        # Main Scrollable / Frame container
        frame = ctk.CTkFrame(self, fg_color="#101929", corner_radius=12, border_width=1, border_color="#1c314d")
        frame.pack(fill="both", expand=True, padx=25, pady=(0, 20))

        # 1. AI Provider Selection
        lbl_provider = ctk.CTkLabel(frame, text="Neural Intelligence Provider:", font=ctk.CTkFont(size=13, weight="bold"), text_color="#a0c0e0")
        lbl_provider.pack(anchor="w", padx=20, pady=(15, 5))

        self.provider_var = ctk.StringVar(value=Config.get_provider())
        provider_menu = ctk.CTkSegmentedButton(
            frame, values=["groq", "openai"],
            variable=self.provider_var,
            command=self._on_provider_change,
            selected_color="#00a8ff", selected_hover_color="#0090db"
        )
        provider_menu.pack(fill="x", padx=20, pady=(0, 10))

        # 2. API Key Entry
        self.lbl_key = ctk.CTkLabel(
            frame, text="API Key (Groq / OpenAI):",
            font=ctk.CTkFont(size=13, weight="bold"), text_color="#a0c0e0"
        )
        self.lbl_key.pack(anchor="w", padx=20, pady=(5, 5))

        current_key = Config.get("GROQ_API_KEY") if self.provider_var.get() == "groq" else Config.get("OPENAI_API_KEY")
        self.key_entry = ctk.CTkEntry(
            frame, show="•", placeholder_text="Enter API key...",
            fg_color="#080e18", border_color="#1f3756"
        )
        self.key_entry.insert(0, current_key)
        self.key_entry.pack(fill="x", padx=20, pady=(0, 10))

        # 3. Model Name
        lbl_model = ctk.CTkLabel(frame, text="Model Identifier:", font=ctk.CTkFont(size=13, weight="bold"), text_color="#a0c0e0")
        lbl_model.pack(anchor="w", padx=20, pady=(5, 5))

        self.model_entry = ctk.CTkEntry(frame, fg_color="#080e18", border_color="#1f3756")
        self.model_entry.insert(0, Config.get_model())
        self.model_entry.pack(fill="x", padx=20, pady=(0, 10))

        # 4. User Honorific / Name
        lbl_name = ctk.CTkLabel(frame, text="User Honorific / Preferred Name:", font=ctk.CTkFont(size=13, weight="bold"), text_color="#a0c0e0")
        lbl_name.pack(anchor="w", padx=20, pady=(5, 5))

        self.name_entry = ctk.CTkEntry(frame, fg_color="#080e18", border_color="#1f3756")
        self.name_entry.insert(0, Config.get_user_name())
        self.name_entry.pack(fill="x", padx=20, pady=(0, 10))

        # 5. Speech Rate Slider
        lbl_rate = ctk.CTkLabel(frame, text="Speech Rate (Words Per Minute):", font=ctk.CTkFont(size=13, weight="bold"), text_color="#a0c0e0")
        lbl_rate.pack(anchor="w", padx=20, pady=(5, 5))

        rate_row = ctk.CTkFrame(frame, fg_color="transparent")
        rate_row.pack(fill="x", padx=20, pady=(0, 10))

        self.rate_slider = ctk.CTkSlider(
            rate_row, from_=120, to=240, number_of_steps=12,
            progress_color="#00e5ff", button_color="#00e5ff",
            command=self._update_rate_label
        )
        self.rate_slider.set(Config.get_voice_rate())
        self.rate_slider.pack(side="left", fill="x", expand=True)

        self.rate_val_lbl = ctk.CTkLabel(rate_row, text=str(Config.get_voice_rate()), width=45, text_color="#00e5ff")
        self.rate_val_lbl.pack(side="right", padx=(10, 0))

        # Bottom Action Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=25, pady=(0, 20))

        btn_test = ctk.CTkButton(
            btn_frame, text="Test Voice", width=120,
            fg_color="#1c314d", hover_color="#27466f",
            command=self._test_voice
        )
        btn_test.pack(side="left")

        btn_cancel = ctk.CTkButton(
            btn_frame, text="Cancel", width=100,
            fg_color="#2b2b36", hover_color="#3d3d4d",
            command=self.destroy
        )
        btn_cancel.pack(side="right", padx=(10, 0))

        btn_save = ctk.CTkButton(
            btn_frame, text="Save Parameters", width=150,
            fg_color="#00a8ff", hover_color="#0090db", text_color="#000000",
            font=ctk.CTkFont(weight="bold"),
            command=self._save
        )
        btn_save.pack(side="right")

    def _update_rate_label(self, val):
        self.rate_val_lbl.configure(text=str(int(val)))

    def _on_provider_change(self, val):
        if val == "groq":
            self.lbl_key.configure(text="Groq API Key (free from console.groq.com):")
            self.model_entry.delete(0, "end")
            self.model_entry.insert(0, "qwen/qwen3.8-27b")
            self.key_entry.delete(0, "end")
            self.key_entry.insert(0, Config.get("GROQ_API_KEY", ""))
        else:
            self.lbl_key.configure(text="OpenAI API Key (platform.openai.com):")
            self.model_entry.delete(0, "end")
            self.model_entry.insert(0, "gpt-4o-mini")
            self.key_entry.delete(0, "end")
            self.key_entry.insert(0, Config.get("OPENAI_API_KEY", ""))

    def _test_voice(self):
        if self.on_test_voice:
            self.on_test_voice("All systems operational. Standing by, Sir.")

    def _save(self):
        provider = self.provider_var.get()
        key = self.key_entry.get().strip()
        model = self.model_entry.get().strip()
        user_name = self.name_entry.get().strip() or "Sir"
        rate = int(self.rate_slider.get())

        updates = {
            "AI_PROVIDER": provider,
            "MODEL_NAME": model,
            "USER_NAME": user_name,
            "VOICE_RATE": rate,
        }

        if provider == "groq":
            updates["GROQ_API_KEY"] = key
        else:
            updates["OPENAI_API_KEY"] = key

        Config.save_settings(updates)

        if self.on_save_callback:
            self.on_save_callback()

        self.destroy()
