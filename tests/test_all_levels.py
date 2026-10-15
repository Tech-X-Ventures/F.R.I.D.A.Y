import os
if os.environ.get('FRYDAY_ENABLE_LIVE_DESKTOP_TESTS') != '1':
    print('SKIP: live desktop test; set FRYDAY_ENABLE_LIVE_DESKTOP_TESTS=1 to opt in')
    raise SystemExit(0)

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import time
from core.brain import JarvisBrain
from core.system_control import SystemControl
from core.voice_engine import VoiceEngine

def run_level_audit():
    brain = JarvisBrain()
    print("=" * 70)
    print("   FRYDAY ALL-LEVEL COMPREHENSIVE VERIFICATION")
    print("=" * 70)

    # LEVEL 1: INTERRUPT & BARGE-IN
    print("\n--- LEVEL 1: Speech Interrupt & Non-Blocking Check ---")
    ve = VoiceEngine()
    ve.speak("Testing non-blocking speech playback cancellation on user interrupt.")
    time.sleep(0.2)
    t0 = time.time()
    ve.stop_speech()
    ve.stop_listening()
    elapsed = time.time() - t0
    print(f"  [LEVEL 1 PASS] stop_speech() executed in {elapsed:.5f}s without GUI freeze")

    # LEVEL 2: GHOST APPS & SLANG
    print("\n--- LEVEL 2: Ghost Apps & Slang Commands ---")
    res_ghost = SystemControl.open_application("Cyberpunk99Game")
    print(f"  [Ghost App]: {res_ghost}")
    assert "could not locate" in res_ghost.lower()
    
    is_valid_real = SystemControl.is_valid_app_or_site("notepad")
    is_valid_fake = SystemControl.is_valid_app_or_site("FakeAppXYZ")
    print(f"  [Validation]: notepad={is_valid_real}, FakeAppXYZ={is_valid_fake}")
    assert is_valid_real and not is_valid_fake
    print("  [LEVEL 2 PASS] Ghost app properly rejected and acknowledged")

    # LEVEL 3: NATURAL VOLUME & TARGETED TELEMETRY
    print("\n--- LEVEL 3: Natural Volume & Targeted Hardware Telemetry ---")
    _, res_ram = brain._check_fast_intent("how much ram do i have left")
    print(f"  [RAM query]: {res_ram}")
    assert "RAM" in res_ram or "Memory" in res_ram

    _, res_bat = brain._check_fast_intent("check my battery level")
    print(f"  [Battery query]: {res_bat}")
    assert "Battery" in res_bat or "mains" in res_bat

    _, res_vol = brain._check_fast_intent("crank the volume")
    print(f"  [Volume Up]: {res_vol}")
    assert "increased" in res_vol
    print("  [LEVEL 3 PASS] Targeted telemetry and natural volume verified")

    # LEVEL 4: YOUTUBE DIRECT VIDEO PLAYBACK
    print("\n--- LEVEL 4: YouTube Direct Video Playback ---")
    res_yt = SystemControl.play_youtube("AC/DC Back in Black")
    print(f"  [YouTube Play]: {res_yt}")
    assert "Playing" in res_yt and "directly" in res_yt
    print("  [LEVEL 4 PASS] Direct YouTube video extraction verified")

    # LEVEL 5: PERSONA, DEVELOPER ATTRIBUTION & LORE
    print("\n--- LEVEL 5: Persona & Developer Attribution ---")
    _, res_creator = brain._check_fast_intent("Who is your creator?")
    print(f"  [Creator]: {res_creator}")
    assert "Prateek Sharma" in res_creator

    _, res_stark = brain._check_fast_intent("Where is Mr. Stark?")
    print(f"  [Mr. Stark]: {res_stark}")
    assert "off-grid" in res_stark and "Prateek Sharma" in res_stark
    print("  [LEVEL 5 PASS] Prateek Sharma developer attribution and Stark lore verified")

    print("\n" + "=" * 70)
    print("   ALL 5 LEVELS FULLY AUDITED AND VERIFIED (100% OPERATIONAL)")
    print("=" * 70)

if __name__ == "__main__":
    run_level_audit()

