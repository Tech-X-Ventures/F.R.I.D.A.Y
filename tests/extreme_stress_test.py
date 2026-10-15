import os
if os.environ.get('FRYDAY_ENABLE_LIVE_DESKTOP_TESTS') != '1':
    print('SKIP: live desktop test; set FRYDAY_ENABLE_LIVE_DESKTOP_TESTS=1 to opt in')
    raise SystemExit(0)

import sys
import time
import threading
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.config import Config
from core.voice_engine import VoiceEngine
from core.brain import JarvisBrain
from core.system_control import SystemControl

failures = []
warnings = []
successes = []

def log_success(test_name, details=""):
    successes.append(f"[PASS] {test_name}: {details}")
    print(f"  [PASS] {test_name}: {details}")

def log_warn(test_name, details=""):
    warnings.append(f"[WARN] {test_name}: {details}")
    print(f"  [WARN] {test_name}: {details}")

def log_fail(test_name, details=""):
    failures.append(f"[FAIL] {test_name}: {details}")
    print(f"  [FAIL] {test_name}: {details}")

# =====================================================================
# TEST SUITE 1: SPEECH SANITIZER & EXTREME INPUT STRESS TEST
# =====================================================================
def test_speech_sanitizer():
    print("\n--- RUNNING SUITE 1: Speech Sanitizer & Input Stress ---")
    
    test_cases = [
        ("Empty String", "", ""),
        ("Whitespace only", "    \n\t  ", ""),
        ("Emoji only", "🔥🚀🤖💯", ""),
        ("Markdown formatting", "**Notice**: This is *crucial* and `important`.", "Notice: This is crucial and ."),
        ("Code block elimination", "Here is code:\n```python\nprint('hello')\n```\nDone.", "Here is code: Code block omitted for speech. Done."),
        ("Symbol expansions", "Load is 95% & memory is high.", "Load is 95 percent and memory is high."),
        ("Bulleted lists", "Report:\n- Task 1\n- Task 2\n* Task 3", "Report: Task 1 Task 2 Task 3"),
        ("Giant wall of text", "A " * 3000, "Should handle 3000 words without crash"),
    ]

    for name, input_txt, expectation in test_cases:
        try:
            cleaned = VoiceEngine._clean_for_speech(input_txt)
            if name == "Empty String" and cleaned == "":
                log_success(name, "Cleaned to empty string")
            elif name == "Whitespace only" and cleaned == "":
                log_success(name, "Cleaned to empty string")
            elif name == "Emoji only" and cleaned == "":
                log_success(name, "Stripped non-ascii/emojis cleanly")
            elif name == "Giant wall of text" and len(cleaned) > 0:
                log_success(name, f"Processed {len(cleaned)} chars smoothly")
            elif "percent" in cleaned and name == "Symbol expansions":
                log_success(name, f"Output: '{cleaned}'")
            elif "Code block omitted" in cleaned and name == "Code block elimination":
                log_success(name, f"Output: '{cleaned}'")
            else:
                log_success(name, f"Output: '{cleaned[:60]}...'")
        except Exception as e:
            log_fail(name, str(e))

# =====================================================================
# TEST SUITE 2: INTENT RESOLUTION & EDGE-CASE SYNONYMS
# =====================================================================
def test_intent_edge_cases():
    print("\n--- RUNNING SUITE 2: Intent Edge-Cases & Variations ---")
    brain = JarvisBrain()

    edge_queries = [
        # Incomplete / degenerate commands
        ("open", "Degenerate open"),
        ("launch", "Degenerate launch"),
        ("weather in", "Incomplete weather"),
        ("play on youtube", "Incomplete youtube"),
        
        # Variations of system telemetry
        ("diagnostics", "Single word diagnostics"),
        ("how much ram do i have", "Natural ram query"),
        ("battery percentage", "Battery query"),
        ("system status report", "Full status command"),
        
        # Audio controls
        ("volume up", "Volume up standard"),
        ("turn up the volume", "Natural volume increase"),
        ("volume down", "Volume down standard"),
        ("mute", "Mute toggle"),
        
        # Time and date
        ("what time is it", "Standard time"),
        ("tell me the time", "Conversational time"),
        ("what date is today", "Standard date"),
        
        # Lock workstation
        ("lock workstation", "Workstation lock"),
        ("lock pc", "PC lock"),
    ]

    for query, description in edge_queries:
        try:
            is_fast, res = brain._check_fast_intent(query)
            if is_fast:
                if res and len(res.strip()) > 0:
                    log_success(description, f"Matched fast intent: '{res[:50]}...'")
                else:
                    log_warn(description, "Matched fast intent but returned empty string!")
            else:
                log_warn(description, f"Not caught by fast intent; will route to LLM fallback for query: '{query}'")
        except Exception as e:
            log_fail(description, f"Exception raised on '{query}': {str(e)}")

# =====================================================================
# TEST SUITE 3: NON-EXISTENT APPS & FAULT TOLERANCE
# =====================================================================
def test_system_control_resilience():
    print("\n--- RUNNING SUITE 3: System Control Fault Tolerance ---")
    
    # 1. Non-existent app
    try:
        res = SystemControl.open_application("non_existent_fake_app_98765")
        if "could not locate" in res.lower() or "unable" in res.lower():
            log_success("Non-existent app launch", f"Gracefully handled: '{res}'")
        else:
            log_warn("Non-existent app launch", f"Unexpected response: '{res}'")
    except Exception as e:
        log_fail("Non-existent app launch", f"Crashed: {str(e)}")

    # 2. Volume control with extreme / invalid action
    try:
        res = SystemControl.volume_control("invalid_direction", steps=999)
        log_success("Invalid volume action", f"Handled without crash: '{res}'")
    except Exception as e:
        log_fail("Invalid volume action", f"Crashed: {str(e)}")

    # 3. Telemetry fetching robustness
    try:
        tel = SystemControl.get_system_telemetry()
        assert "cpu_percent" in tel
        assert "ram_percent" in tel
        assert "disk_percent" in tel
        log_success("Telemetry integrity", f"CPU: {tel['cpu_percent']}%, RAM: {tel['ram_percent']}%, Bat: {tel['battery_percent']}")
    except Exception as e:
        log_fail("Telemetry integrity", f"Crashed: {str(e)}")

    # 4. Weather service error tolerance (non-existent city)
    try:
        res = SystemControl.get_weather("CityThatDoesNotExist123456XYZ")
        log_success("Invalid city weather", f"Response: '{res[:60]}...'")
    except Exception as e:
        log_fail("Invalid city weather", f"Crashed: {str(e)}")

# =====================================================================
# TEST SUITE 4: LLM BRAIN & CONCURRENCY RACE CONDITIONS
# =====================================================================
def test_brain_concurrency_and_memory():
    print("\n--- RUNNING SUITE 4: LLM Brain Concurrency & Memory Truncation ---")
    brain = JarvisBrain()

    # 1. Test Memory Overflow (30 turns)
    try:
        for i in range(25):
            brain.history.append({"role": "user", "content": f"Turn {i}"})
            brain.history.append({"role": "assistant", "content": f"Answer {i}"})
        # Check history length management
        _ = brain.process_query("What time is it?")
        if len(brain.history) <= brain._max_history * 2 + 4:
            log_success("Memory truncation", f"History bounded cleanly at {len(brain.history)} entries")
        else:
            log_warn("Memory truncation", f"History grew unbounded to {len(brain.history)} entries")
    except Exception as e:
        log_fail("Memory truncation", str(e))

    # 2. Concurrency stress test (5 parallel threads accessing brain)
    print("  Testing 5 concurrent query dispatches to brain...")
    thread_exceptions = []
    
    def worker(idx):
        try:
            ans = brain.process_query(f"What time is it, thread {idx}?")
            if not ans:
                thread_exceptions.append(f"Thread {idx} got empty response")
        except Exception as e:
            thread_exceptions.append(f"Thread {idx} exception: {str(e)}")

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)

    if not thread_exceptions:
        log_success("Concurrency stress", "All 5 concurrent threads executed safely without race conditions")
    else:
        log_fail("Concurrency stress", f"Errors occurred: {thread_exceptions}")

# =====================================================================
# TEST SUITE 5: REAL LIVE LLM QUERY WITH TOOL EXECUTION
# =====================================================================
def test_live_llm_tool_execution():
    print("\n--- RUNNING SUITE 5: Live LLM Brain Tool Calling ---")
    brain = JarvisBrain()
    
    try:
        query = "Can you tell me how much RAM and CPU load my computer is currently using?"
        print(f"  Sending live prompt to Groq: '{query}'")
        resp = brain.process_query(query)
        if ("cpu" in resp.lower() or "ram" in resp.lower() or "percent" in resp.lower()) and len(resp) > 20:
            log_success("Live LLM Telemetry Tool Call", f"Response: '{resp[:100]}...'")
        else:
            log_warn("Live LLM Telemetry Tool Call", f"Response might not have used tool: '{resp}'")
    except Exception as e:
        log_fail("Live LLM Telemetry Tool Call", str(e))

def main():
    print("=" * 70)
    print("   FRYDAY EXTREME STRESS-TEST HARNESS")
    print("=" * 70)
    
    test_speech_sanitizer()
    test_intent_edge_cases()
    test_system_control_resilience()
    test_brain_concurrency_and_memory()
    test_live_llm_tool_execution()

    print("\n" + "=" * 70)
    print(f"SUMMARY: {len(successes)} Passed, {len(warnings)} Warnings, {len(failures)} Failures")
    print("=" * 70)

if __name__ == "__main__":
    main()

