"""Safe website-intent routing checks. Never starts a browser."""
import sys
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.brain import JarvisBrain
from core.system_control import SystemControl


def run_tests():
    brain = JarvisBrain()
    queries = ["open google maps on chrome", "open github", "open youtube"]
    with patch.object(SystemControl, "open_website", return_value="Opened website") as open_site, \
         patch.object(SystemControl, "open_application", return_value="Opened app") as open_app:
        for query in queries:
            handled, response = brain._check_fast_intent(query)
            assert handled and response, f"Not handled: {query}"
        assert open_site.call_count + open_app.call_count >= 1
    print("PASS: Website/app intent routing (mocked; no browser launched)")


if __name__ == "__main__":
    run_tests()
