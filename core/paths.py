"""Runtime paths for source and installed FRYDAY builds."""
import os
import sys
from pathlib import Path

APP_NAME = "FRYDAY"
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def app_data_dir(environ=None, frozen=None) -> Path:
    """Return the per-user FRYDAY data root for installed builds."""
    env = os.environ if environ is None else environ
    frozen = is_frozen() if frozen is None else frozen
    if not frozen:
        return PROJECT_ROOT
    roaming = env.get("APPDATA") or (Path.home() / "AppData" / "Roaming")
    return Path(roaming) / APP_NAME


def config_file(environ=None, frozen=None) -> Path:
    """Source builds use the project .env; installed builds use user config."""
    root = app_data_dir(environ=environ, frozen=frozen)
    return root / ".env"


def data_dir(environ=None, frozen=None) -> Path:
    """Keep installed user data outside the replaceable application folder."""
    root = app_data_dir(environ=environ, frozen=frozen)
    return root / "data"
