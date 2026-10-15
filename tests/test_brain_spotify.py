"""Safe Spotify intent test; does not launch Spotify or change playback."""
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core import memory
from core.brain import JarvisBrain


def run_tests():
    with tempfile.TemporaryDirectory(prefix="fryday-spotify-test-") as temp_dir:
        data = Path(temp_dir) / "data"
        memory.DATA_DIR = data
        memory.PROFILE_FILE = data / "user_profile.json"
        memory.CHAT_MEMORY_FILE = data / "chat_memory.json"
        brain = JarvisBrain()
        with patch("core.system_control.SystemControl.play_spotify", return_value="Mock playback started") as play:
            for query in (
                "play starboy on spotify",
                "play kesariya on spotify",
                "play shape of you on spotify",
                "play Yalgaar song on Spotify",
            ):
                handled, response = brain._check_fast_intent(query)
                assert handled, f"Spotify intent was not handled: {query}"
                assert response
            assert play.call_count == 4, f"Expected 4 mocked playback calls, got {play.call_count}"
            assert play.call_args.args == ("yalgaar",), play.call_args
        print("PASS: Spotify intent routing (mocked; no playback launched)")


if __name__ == "__main__":
    run_tests()
