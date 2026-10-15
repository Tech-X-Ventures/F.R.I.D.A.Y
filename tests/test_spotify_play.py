"""Safe test entry point for Spotify intents; real playback is never started."""
import sys
from pathlib import Path
from unittest.mock import Mock, patch

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.brain import JarvisBrain
from core.system_control import SystemControl, _send_spotify_search_keys


def run_tests():
    shell = Mock()
    with patch("core.system_control.time.sleep"):
        _send_spotify_search_keys(shell, "Yalgaar")
    sent_keys = [entry.args[0] for entry in shell.SendKeys.call_args_list]
    assert sent_keys == ["^k", "^a", "{DELETE}", "Yalgaar", "{DOWN}", "{ENTER}"], sent_keys

    with patch("win32com.client.Dispatch") as dispatch, \
         patch("core.system_control.psutil.process_iter", return_value=[]), \
         patch("core.system_control.os.startfile") as start_spotify, \
         patch("core.system_control._focus_spotify_window", return_value=True), \
         patch("core.system_control._send_spotify_search_keys") as select_result:
        result = SystemControl.play_spotify("Yalgaar")
    start_spotify.assert_called_once_with("spotify:")
    select_result.assert_called_once_with(dispatch.return_value, "Yalgaar")
    assert "selected the first match" in result

    brain = JarvisBrain()
    with patch("core.system_control.SystemControl.play_spotify", return_value="Mock playback started") as play:
        handled, response = brain._check_fast_intent("play starboy the weeknd on spotify")
        assert handled and response
        assert play.call_count == 1
    print("PASS: Spotify search selects first match, then confirms (mocked; no playback launched)")


if __name__ == "__main__":
    run_tests()
