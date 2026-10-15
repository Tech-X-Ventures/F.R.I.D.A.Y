import os
from pathlib import Path
from dotenv import load_dotenv
from core.paths import config_file

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = config_file()

# Load initial environment
load_dotenv(dotenv_path=ENV_PATH)

class Config:
    @staticmethod
    def get(key: str, default: str = "") -> str:
        return os.getenv(key, default)

    @classmethod
    def get_provider(cls) -> str:
        return cls.get("AI_PROVIDER", "groq").lower().strip()

    @classmethod
    def get_api_key(cls) -> str:
        provider = cls.get_provider()
        if provider == "groq":
            return cls.get("GROQ_API_KEY", "").strip()
        return cls.get("OPENAI_API_KEY", "").strip()

    @classmethod
    def get_model(cls) -> str:
        provider = cls.get_provider()
        default_model = "qwen/qwen3.8-27b" if provider == "groq" else "gpt-4o-mini"
        return cls.get("MODEL_NAME", default_model).strip()

    @classmethod
    def get_user_name(cls) -> str:
        return cls.get("USER_NAME", "Sir").strip()

    @classmethod
    def get_voice_rate(cls) -> int:
        try:
            return int(cls.get("VOICE_RATE", "180"))
        except ValueError:
            return 180

    @classmethod
    def get_voice_volume(cls) -> float:
        try:
            return float(cls.get("VOICE_VOLUME", "1.0"))
        except ValueError:
            return 1.0

    @classmethod
    def get_voice_index(cls) -> int:
        try:
            return int(cls.get("VOICE_INDEX", "0"))
        except ValueError:
            return 0

    @classmethod
    def save_settings(cls, updates: dict):
        """Update .env file and active environment variables."""
        ENV_PATH.parent.mkdir(parents=True, exist_ok=True)
        current_lines = []
        if ENV_PATH.exists():
            with open(ENV_PATH, "r", encoding="utf-8") as f:
                current_lines = f.readlines()

        key_found = {k: False for k in updates.keys()}
        new_lines = []

        for line in current_lines:
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and "=" in stripped:
                k = stripped.split("=", 1)[0].strip()
                if k in updates:
                    new_lines.append(f"{k}={updates[k]}\n")
                    key_found[k] = True
                    os.environ[k] = str(updates[k])
                    continue
            new_lines.append(line)

        for k, found in key_found.items():
            if not found:
                new_lines.append(f"{k}={updates[k]}\n")
                os.environ[k] = str(updates[k])

        with open(ENV_PATH, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
