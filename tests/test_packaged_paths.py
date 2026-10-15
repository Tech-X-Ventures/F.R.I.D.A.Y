"""Check installed-build paths and first-run API-key persistence."""
import os
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.paths import app_data_dir, config_file, data_dir
from gui.api_key_setup import save_api_credentials
from gui.app import JarvisApp


def run_tests():
    with tempfile.TemporaryDirectory(prefix="fryday-path-test-") as temp_dir:
        env = {"APPDATA": temp_dir}
        expected = Path(temp_dir) / "FRYDAY"
        assert app_data_dir(env, frozen=True) == expected
        assert config_file(env, frozen=True) == expected / ".env"
        assert data_dir(env, frozen=True) == expected / "data"
        assert app_data_dir(env, frozen=False) == PROJECT_ROOT

        settings_file = expected / ".env"
        with patch("core.config.ENV_PATH", settings_file), patch.dict(os.environ, {}, clear=False):
            save_api_credentials("groq", "test-key-do-not-use")
            saved = settings_file.read_text(encoding="utf-8")
            assert "AI_PROVIDER=groq" in saved
            assert "GROQ_API_KEY=test-key-do-not-use" in saved
            assert "OPENAI_API_KEY=test-key-do-not-use" not in saved
            try:
                save_api_credentials("groq", "   ")
            except ValueError:
                pass
            else:
                raise AssertionError("Empty API keys must be rejected")

        fake_app = SimpleNamespace(after=lambda _delay, callback: callback())
        fake_app._initial_greeting = lambda: setattr(fake_app, "greeting_started", True)
        with patch("core.config.Config.get_api_key", return_value="") as get_key, \
             patch("gui.api_key_setup.APIKeySetupDialog") as setup_dialog:
            JarvisApp._check_first_run_setup(fake_app)
        get_key.assert_called_once_with()
        setup_dialog.assert_called_once()
        setup_dialog.call_args.kwargs["on_complete"]()
        assert fake_app.greeting_started

        fake_app.greeting_started = False
        with patch("core.config.Config.get_api_key", return_value="configured-key"), \
             patch("gui.api_key_setup.APIKeySetupDialog") as setup_dialog:
            JarvisApp._check_first_run_setup(fake_app)
        setup_dialog.assert_not_called()
        assert fake_app.greeting_started

    print("PASS: installed data paths and API-key persistence (temporary test data)")


if __name__ == "__main__":
    run_tests()
