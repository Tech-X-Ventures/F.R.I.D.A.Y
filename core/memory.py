import os
import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from core.paths import data_dir

# Base directory for memory data
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = data_dir()
PROFILE_FILE = DATA_DIR / "user_profile.json"
CHAT_MEMORY_FILE = DATA_DIR / "chat_memory.json"

DEFAULT_PROFILE = {
    "name": "User",
    "preferred_title": "Sir",
    "role": "Software Developer & Creator of FRYDAY",
    "city": "Delhi",
    "birthday": "Not specified yet",
    "tech_stack": [
        "Python",
        "AI/ML",
        "Automation",
        "System Programming"
    ],
    "goals": [
        "Building an advanced, fully autonomous personal desktop AI assistant",
        "Mastering AI engineering and intelligent systems"
    ],
    "favorites": {
        "music_genre": "Rock, Synthwave, Lo-Fi, Bollywood",
        "favorite_artists": "Queen, AC/DC, A.R. Rahman",
        "favorite_apps": ["VS Code", "Chrome", "Notepad", "Command Prompt"]
    },
    "workstyle": {
        "routine": "Flexible developer schedule, often coding late nights",
        "tone_preference": "Refined British butler, loyal, witty, subtly humorous"
    },
    # Custom memories are personal facts, not boot-time tasks or briefing items.
    "custom_memories": []
}


class MemoryManager:
    """
    Thread-safe persistent memory manager for FRYDAY.
    Handles:
      1. User Profile (Identity, Preferences, Favorites, Custom facts)
      2. Chat Memory (Persistent conversation history across restarts)
    """
    _lock = threading.Lock()

    @classmethod
    def _ensure_data_dir(cls):
        """Ensure the data directory and default profile file exist."""
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if not PROFILE_FILE.exists():
            cls._save_json(PROFILE_FILE, DEFAULT_PROFILE)
        if not CHAT_MEMORY_FILE.exists():
            cls._save_json(CHAT_MEMORY_FILE, {"conversations": [], "last_active": datetime.now().isoformat()})

    @classmethod
    def _read_json(cls, filepath: Path) -> Dict[str, Any]:
        with cls._lock:
            try:
                if not filepath.exists():
                    return {}
                with open(filepath, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}

    @classmethod
    def _save_json(cls, filepath: Path, data: Dict[str, Any]):
        with cls._lock:
            try:
                DATA_DIR.mkdir(parents=True, exist_ok=True)
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
            except Exception as e:
                print(f"[MemoryManager Error] Failed to write to {filepath}: {e}")

    @classmethod
    def load_profile(cls) -> Dict[str, Any]:
        """Load user profile dictionary."""
        cls._ensure_data_dir()
        profile = cls._read_json(PROFILE_FILE)
        if not profile:
            profile = DEFAULT_PROFILE.copy()
            cls._save_json(PROFILE_FILE, profile)
        return profile

    @classmethod
    def save_profile(cls, profile_data: Dict[str, Any]):
        """Save user profile dictionary to disk."""
        cls._ensure_data_dir()
        cls._save_json(PROFILE_FILE, profile_data)

    @classmethod
    def get_profile_context(cls) -> str:
        """
        Format the user profile into a rich, concise prompt section for the LLM brain.
        """
        p = cls.load_profile()
        name = p.get("name", "User")
        title = p.get("preferred_title", "Sir")
        role = p.get("role", "Developer")
        city = p.get("city", "")
        tech = ", ".join(p.get("tech_stack", []))
        goals = "; ".join(p.get("goals", []))
        favorites = p.get("favorites", {})
        music = favorites.get("music_genre", "")
        artists = favorites.get("favorite_artists", "")
        custom_facts = "\n".join([f"- {fact}" for fact in p.get("custom_memories", [])])

        context = (
            f"KNOWLEDGE BASE ABOUT YOUR CREATOR & USER:\n"
            f"- Name: {name}\n"
            f"- Preferred Salutation: '{title}'\n"
            f"- Role & Status: {role}\n"
            f"- Base Location/City: {city if city else 'Not specified'}\n"
            f"- Primary Tech Stack: {tech}\n"
            f"- Current Goals: {goals}\n"
            f"- Music & Artists: {music} (Artists: {artists})\n"
            f"Permanent Memories & Known Facts:\n{custom_facts}\n"
            f"Always prioritize this personal context when formulating responses or executing personalized requests."
        )
        return context

    @classmethod
    def add_custom_memory(cls, fact: str) -> str:
        """
        Add a new memory or fact told by the user to permanent storage.
        """
        clean_fact = fact.strip().rstrip(".?!")
        if not clean_fact:
            return "No information provided to remember, Sir."

        profile = cls.load_profile()
        memories = profile.setdefault("custom_memories", [])

        # Avoid exact duplicates
        if clean_fact not in memories:
            memories.append(clean_fact)
            cls.save_profile(profile)

        return f"I have committed that to permanent memory, Sir: '{clean_fact}'."

    @classmethod
    def get_custom_memories(cls) -> List[str]:
        """Return list of custom facts remembered."""
        profile = cls.load_profile()
        return profile.get("custom_memories", [])

    @classmethod
    def remove_custom_memory_by_index(cls, index: int) -> str:
        """
        Remove a memory by 1-based index (as spoken: 'delete task 2').
        Returns a confirmation string.
        """
        profile = cls.load_profile()
        memories = profile.get("custom_memories", [])
        if not memories:
            return "There are no pending tasks to remove, Sir."
        if index < 1 or index > len(memories):
            return f"I don't have a task number {index} on record, Sir."
        removed = memories.pop(index - 1)
        profile["custom_memories"] = memories
        cls.save_profile(profile)
        return f"Task {index} has been marked complete and removed from the briefing, Sir: '{removed}'."

    @classmethod
    def remove_custom_memory_by_keyword(cls, keyword: str) -> str:
        """
        Remove first memory that contains the keyword (case-insensitive).
        """
        profile = cls.load_profile()
        memories = profile.get("custom_memories", [])
        kw = keyword.strip().lower()
        for i, m in enumerate(memories):
            if kw in m.lower():
                removed = memories.pop(i)
                profile["custom_memories"] = memories
                cls.save_profile(profile)
                return f"Removed from briefing list, Sir: '{removed}'."
        return f"No pending task matching '{keyword}' found, Sir."

    @classmethod
    def clear_all_memories(cls) -> str:
        """Wipe all custom memories / pending tasks."""
        profile = cls.load_profile()
        count = len(profile.get("custom_memories", []))
        profile["custom_memories"] = []
        cls.save_profile(profile)
        return f"All {count} pending tasks cleared, Sir. Briefing slate is clean."

    @classmethod
    def update_profile_field(cls, key: str, value: Any) -> str:
        """Update a specific top-level or nested profile attribute."""
        profile = cls.load_profile()
        if "." in key:
            parts = key.split(".")
            d = profile
            for p in parts[:-1]:
                d = d.setdefault(p, {})
            d[parts[-1]] = value
        else:
            profile[key] = value
        cls.save_profile(profile)
        return f"Updated profile field '{key}' successfully, Sir."

    @classmethod
    def save_chat_turn(cls, role: str, content: str, max_stored: int = 50):
        """Append a conversation message to persistent chat memory."""
        cls._ensure_data_dir()
        data = cls._read_json(CHAT_MEMORY_FILE)
        convs = data.get("conversations", [])
        convs.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        # Keep recent bounded turns
        if len(convs) > max_stored:
            convs = convs[-max_stored:]
        data["conversations"] = convs
        data["last_active"] = datetime.now().isoformat()
        cls._save_json(CHAT_MEMORY_FILE, data)

    @classmethod
    def load_recent_chats(cls, limit: int = 10) -> List[Dict[str, str]]:
        """
        Load the most recent conversation turns formatted for LLM history.
        """
        cls._ensure_data_dir()
        data = cls._read_json(CHAT_MEMORY_FILE)
        convs = data.get("conversations", [])
        recent = convs[-limit:] if limit and len(convs) > limit else convs
        return [{"role": c["role"], "content": c["content"]} for c in recent]

    @classmethod
    def clear_chat_history(cls) -> str:
        """Clear persistent conversation history while retaining profile."""
        cls._ensure_data_dir()
        cls._save_json(CHAT_MEMORY_FILE, {
            "conversations": [],
            "last_active": datetime.now().isoformat()
        })
        return "Conversation history has been cleared from memory, Sir. Profile memories remain intact."
