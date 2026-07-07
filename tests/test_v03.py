"""Zero OS v0.3 — Integration Test"""
import sys
import os
# Project root is parent of tests/
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

# Use in-memory DB to avoid touching production data
os.environ["ZERO_TEST"] = "1"

from core.memory.database import DatabaseManager
from core.memory.memory_store import MemoryStore
from core.brain.intent_engine import IntentEngine
from core.brain.decision_engine import DecisionEngine
from core.brain.personality import PersonalityManager
from core.planner.task_planner import TaskPlanner
from core.reflection.reflection_engine import ReflectionEngine
from core.goals import GoalsManager
from core.state.zero_state import ZeroState

print("=== ALL v0.3 IMPORTS PASSED ===")

# Instantiate all modules with temp DB (not :memory: since each connect() creates a new DB)
import tempfile
_test_db_path = os.path.join(tempfile.gettempdir(), "zero_test_v03.db")
# Clean up any previous test DB
if os.path.exists(_test_db_path):
    os.remove(_test_db_path)

db = DatabaseManager(db_path=_test_db_path)
ms = MemoryStore(db)
st = ZeroState()
ie = IntentEngine()
gm = GoalsManager(db)
tp = TaskPlanner(goals_manager=gm, memory_store=ms)
de = DecisionEngine(ie, ms, gm, st)
re_ = ReflectionEngine(ms, goals_manager=gm, state=st)
pm = PersonalityManager()

print("=== ALL v0.3 MODULES INSTANTIATED ===")

# Test 1: Session management
ms.start_session(st.session_id)
print(f"[PASS] Session started: {st.session_id}")

# Test 2: Short-term memory
ms.push_turn("user", "hello zero")
ms.push_turn("assistant", "Hello Varun!")
ctx = ms.get_conversation_context()
assert len(ctx) == 2, f"Expected 2 turns, got {len(ctx)}"
print(f"[PASS] Short-term memory: {len(ctx)} turns")

# Test 3: Long-term memory
ms.save_fact("language", "Python")
facts = ms.recall_facts("language")
assert len(facts) >= 1, "No facts found"
print(f"[PASS] Long-term facts: {len(facts)} found")

# Test 4: Goal system
g_id = db.add_goal("Master ML", "2027-01-01")
db.update_goal_priority(g_id, "high")
db.update_goal_progress(g_id, 35, "Complete CNN project")
goals = db.get_goals()
assert len(goals) >= 1, "No goals found"
g = goals[-1]
assert len(g) >= 7, f"Expected 7 columns, got {len(g)}"
print(f"[PASS] Goal system: {g[1]} | priority={g[4]} | progress={g[5]}% | next={g[6]}")

# Test 5: Goals Manager
top = gm.get_top_priority_goal()
assert top is not None, "No top goal"
print(f"[PASS] Top priority goal: {top['description']}")

report = gm.get_goal_status_report()
assert len(report) >= 1, "Empty report"
print(f"[PASS] Goal status report: {len(report)} goals")

recs = gm.get_daily_recommendation()
print(f"[PASS] Daily recommendations: {len(recs)} items")

# Test 6: Decision Engine - thinking question
result = de.process("what should I do now")
assert result["type"] == "decision", f"Expected 'decision', got {result['type']}"
print(f"[PASS] Decision engine (thinking): type={result['type']}, intent={result['intent']}")

# Test 7: Decision Engine - direct command
result2 = de.process("open chrome")
assert result2["type"] == "command", f"Expected 'command', got {result2['type']}"
print(f"[PASS] Decision engine (command): type={result2['type']}")

# Test 8: Decision Engine - time planning
result3 = de.process("I have 2 hours free")
assert result3["type"] == "decision", f"Expected 'decision', got {result3['type']}"
print(f"[PASS] Decision engine (time plan): intent={result3['intent']}")

# Test 9: Decision Engine - status report
result4 = de.process("how am I doing")
assert result4["type"] == "decision"
assert "GOALS" in result4["response"]
print(f"[PASS] Decision engine (status report): {len(result4['response'])} chars")

# Test 10: Reflection - startup briefing
briefing = re_.generate_startup_briefing()
assert len(briefing) > 0, "Empty briefing"
assert "Varun" in briefing, "Briefing doesn't address Varun"
print(f"[PASS] Startup briefing: {len(briefing)} chars")

# Test 11: Reflection - session wrapup
st.record_command("test command", "chat")
wrapup = re_.generate_session_wrapup()
assert "Varun" in wrapup
print(f"[PASS] Session wrapup: {len(wrapup)} chars")

# Test 12: State tracker
assert st.commands_this_session == 1
snap = st.get_snapshot()
assert "session_id" in snap
assert snap["commands_processed"] == 1
print(f"[PASS] State tracker: {st.commands_this_session} commands, {st.get_session_duration_minutes()} min")

# Test 13: Task Planner (goal-aware)
actions = [{"action": "search_web", "params": {"query": "ML study"}, "response": "Searching"}]
plan = tp.plan_steps(actions)
assert len(plan) >= 2, "Plan should inject wifi check"
print(f"[PASS] Task planner: {len(plan)} steps (includes injected checks)")

# Test 14: Context save and restore
ms.save_session_context(snap)
continuity = ms.get_continuity_summary()
assert continuity is not None, "No continuity summary"
print(f"[PASS] Session context saved and restored")

# Test 15: Personality enhancement
enhanced = pm.enhance_response("Chrome is open.", action_type="open_app", params={"app_name": "chrome"})
assert "Varun" in enhanced
print(f"[PASS] Personality enhancement working")

print()
print("=" * 50)
print("  ALL 15 v0.3 TESTS PASSED [OK]")
print("=" * 50)
