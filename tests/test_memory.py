import sys
import tempfile
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core import memory as memory_module
from core.memory import MemoryManager
from core.brain import JarvisBrain

def run_memory_tests():
    print("=" * 70)
    print("   FRYDAY PERSISTENT MEMORY & USER PROFILE VERIFICATION")
    print("=" * 70)

    # 1. Profile Loading & Verification
    print("\n--- TEST 1: Profile Initialization & Structure ---")
    profile = MemoryManager.load_profile()
    assert memory_module.PROFILE_FILE.exists(), "Profile file should exist"
    assert profile["name"] == "Prateek Sharma", "Name should be Prateek Sharma"
    assert "Python" in profile["tech_stack"], "Tech stack should contain Python"
    print(f"  [Profile Name]: {profile['name']}")
    print(f"  [Preferred Title]: {profile['preferred_title']}")
    print(f"  [Role]: {profile['role']}")
    print(f"  [City]: {profile['city']}")
    print("  [TEST 1 PASS] User profile successfully initialized and verified.")

    # 2. Dynamic Memory Recording
    print("\n--- TEST 2: Dynamic Memory Recording ('Remember That') ---")
    test_fact = "Prateek likes drinking cold brew coffee while building AI"
    res_add = MemoryManager.add_custom_memory(test_fact)
    print(f"  [Memory Add Result]: {res_add}")
    assert test_fact in MemoryManager.get_custom_memories(), "Fact should be saved in memories"
    print("  [TEST 2 PASS] Dynamic fact successfully added to permanent storage.")

    # 3. Brain Fast Intent Memory Integration
    print("\n--- TEST 3: Brain Fast-Intent Memory Queries ---")
    brain = JarvisBrain()
    
    # Test 'remember that' via brain
    fast_handled, res_brain_mem = brain._check_fast_intent("remember that I have an AI demo next Tuesday")
    assert fast_handled, "Brain should handle 'remember that' directly"
    print(f"  [Brain Remember]: {res_brain_mem}")
    assert "committed that to permanent memory" in res_brain_mem.lower()

    # Test 'who am i'
    fast_handled, res_who = brain._check_fast_intent("who am i")
    assert fast_handled, "Brain should handle 'who am i'"
    print(f"  [Brain Who Am I]:\n{res_who}")
    assert "Prateek Sharma" in res_who

    # Test 'what do you know about me'
    fast_handled, res_know = brain._check_fast_intent("what do you know about me")
    assert fast_handled
    assert "Prateek Sharma" in res_know
    print("  [TEST 3 PASS] Brain fast-intent memory queries verified.")

    # 4. Chat Memory Persistence Across Sessions
    print("\n--- TEST 4: Chat History Persistence ---")
    # Simulate a conversation
    brain._add_to_history("user", "Hello Jarvis, calibrate all subroutines")
    brain._add_to_history("assistant", "All systems are functioning within normal parameters, Sir.")

    recent = MemoryManager.load_recent_chats(limit=5)
    assert len(recent) >= 2, "Chat history should contain recorded turns"
    assert memory_module.CHAT_MEMORY_FILE.exists(), "Chat memory file should exist"
    print(f"  [Recent turns count in storage]: {len(recent)}")
    print(f"  [Latest turn]: {recent[-1]['role']} -> {recent[-1]['content'][:50]}...")
    print("  [TEST 4 PASS] Multi-session chat persistence confirmed.")

    # 5. Profile Context Injection in System Prompt
    print("\n--- TEST 5: LLM System Prompt Memory Injection ---")
    system_prompt = brain.get_system_prompt()
    assert "Prateek Sharma" in system_prompt
    assert "KNOWLEDGE BASE ABOUT YOUR CREATOR" in system_prompt
    assert profile.get("city") in system_prompt
    print("  [System Prompt Context Checked]: Personal profile context successfully embedded.")
    print("  [TEST 5 PASS] LLM Prompt has full awareness of user profile.")

    print("\n" + "=" * 70)
    print("   ALL MEMORY SYSTEMS VERIFIED (100% OPERATIONAL)")
    print("=" * 70)

if __name__ == "__main__":
    with tempfile.TemporaryDirectory(prefix="fryday-memory-test-") as temp_dir:
        data_dir = Path(temp_dir) / "data"
        memory_module.DATA_DIR = data_dir
        memory_module.PROFILE_FILE = data_dir / "user_profile.json"
        memory_module.CHAT_MEMORY_FILE = data_dir / "chat_memory.json"
        run_memory_tests()
