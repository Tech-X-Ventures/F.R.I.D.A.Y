"""First-run API key setup for installed FRYDAY builds."""
import webbrowser

import customtkinter as ctk

from core.config import Config


def save_api_credentials(provider: str, key: str):
    """Save a user's key through the active source/installed config path."""
    normalized = provider.strip().lower()
    if normalized not in {"groq", "openai"}:
        raise ValueError("Unsupported AI provider")
    clean_key = key.strip()
    if not clean_key:
        raise ValueError("API key cannot be empty")
    key_name = "GROQ_API_KEY" if normalized == "groq" else "OPENAI_API_KEY"
    model = "qwen/qwen3.8-27b" if normalized == "groq" else "gpt-4o-mini"
    Config.save_settings({"AI_PROVIDER": normalized, "MODEL_NAME": model, key_name: clean_key})


class APIKeySetupDialog(ctk.CTkToplevel):
    def __init__(self, parent, on_complete):
        super().__init__(parent)
        self.on_complete = on_complete
        self.title("FRYDAY // AI Setup")
        self.geometry("470x350")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._continue_without_key)
        self.configure(fg_color="#0b111e")

        ctk.CTkLabel(
            self, text="CONNECT FRYDAY TO AI",
            font=ctk.CTkFont(family="Consolas", size=20, weight="bold"),
            text_color="#00e5ff",
        ).pack(pady=(24, 8))
        ctk.CTkLabel(
            self,
            text="Add your own API key to enable AI conversation.\nYour key stays on this Windows account and is not part of the installer.",
            justify="center", text_color="#a0c0e0",
        ).pack(pady=(0, 18))

        self.provider_var = ctk.StringVar(value="groq")
        self.provider_menu = ctk.CTkSegmentedButton(
            self, values=["groq", "openai"], variable=self.provider_var,
            command=self._provider_changed,
            selected_color="#00a8ff", selected_hover_color="#0090db",
        )
        self.provider_menu.pack(fill="x", padx=35, pady=(0, 12))

        self.key_entry = ctk.CTkEntry(
            self, show="•", placeholder_text="Paste your Groq API key",
            fg_color="#080e18", border_color="#1f3756",
        )
        self.key_entry.pack(fill="x", padx=35, pady=(0, 8))

        self.key_link = ctk.CTkButton(
            self, text="Get a Groq API key", height=28,
            fg_color="transparent", hover_color="#13243a",
            text_color="#00e5ff", command=self._open_key_page,
        )
        self.key_link.pack(pady=(0, 12))

        self.error_label = ctk.CTkLabel(self, text="", text_color="#ff7070")
        self.error_label.pack(pady=(0, 4))

        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.pack(fill="x", padx=35, pady=(4, 16))
        ctk.CTkButton(
            buttons, text="Continue without AI", fg_color="#263244",
            hover_color="#34445a", command=self._continue_without_key,
        ).pack(side="left")
        ctk.CTkButton(
            buttons, text="Save and Continue", fg_color="#00a8ff",
            hover_color="#0090db", text_color="#000000",
            command=self._save_key,
        ).pack(side="right")

        self.bind("<Return>", lambda _event: self._save_key())

    def _provider_changed(self, provider):
        if provider == "groq":
            self.key_entry.configure(placeholder_text="Paste your Groq API key")
            self.key_link.configure(text="Get a Groq API key")
        else:
            self.key_entry.configure(placeholder_text="Paste your OpenAI API key")
            self.key_link.configure(text="Get an OpenAI API key")

    def _open_key_page(self):
        url = (
            "https://console.groq.com/keys"
            if self.provider_var.get() == "groq"
            else "https://platform.openai.com/api-keys"
        )
        webbrowser.open(url)

    def _save_key(self):
        provider = self.provider_var.get()
        key = self.key_entry.get().strip()
        if not key:
            self.error_label.configure(text="Paste your API key, or continue without AI.")
            return

        save_api_credentials(provider, key)
        self._finish()

    def _continue_without_key(self):
        self._finish()

    def _finish(self):
        self.grab_release()
        self.destroy()
        self.on_complete()
