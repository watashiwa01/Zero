import unittest
import os
import sys
from datetime import datetime, timedelta

# Add root folder to path to import core and agents
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.memory import DatabaseManager
from core.memory.memory_store import MemoryStore
from core.brain.intent_engine import IntentEngine
from core.brain.personality import PersonalityManager
from core.planner.task_planner import TaskPlanner
from core.reflection.reflection_engine import ReflectionEngine
from agents.system import SystemAgent

class TestZeroOS(unittest.TestCase):
    def setUp(self):
        # Use a temporary test database
        self.db_path = "test_zero.db"
        self.db = DatabaseManager(db_path=self.db_path)
        self.memory_store = MemoryStore(self.db)
        self.intent_engine = IntentEngine()
        self.task_planner = TaskPlanner()
        self.personality = PersonalityManager()
        self.reflection = ReflectionEngine(self.memory_store)
        self.system = SystemAgent()

    def tearDown(self):
        # Remove test database file
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except PermissionError:
                pass

    def test_database_creation(self):
        self.assertTrue(os.path.exists(self.db_path))

    def test_memory_crud(self):
        mem_id = self.db.save_memory("Varun prefers project based learning", category="preference")
        self.assertIsNotNone(mem_id)

        results = self.db.recall_memories("learning")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][0], "Varun prefers project based learning")

    def test_system_status(self):
        battery_status = self.system.check_battery()
        self.assertIsInstance(battery_status, str)
        self.assertTrue(len(battery_status) > 0)

        wifi_status = self.system.check_wifi()
        self.assertIsInstance(wifi_status, str)
        self.assertTrue(len(wifi_status) > 0)

    # --- New Tests for Phase 2 ---
    def test_intent_engine_single_action(self):
        resp = self.intent_engine._rule_based_fallback("open chrome")
        self.assertEqual(resp["intent"], "single_action")
        self.assertEqual(len(resp["actions"]), 1)
        self.assertEqual(resp["actions"][0]["action"], "open_app")
        self.assertEqual(resp["actions"][0]["params"]["app_name"], "chrome")

    def test_intent_engine_multi_action(self):
        resp = self.intent_engine._rule_based_fallback("open chrome and remember that my exam is on Monday")
        self.assertEqual(resp["intent"], "multi_action")
        self.assertEqual(len(resp["actions"]), 2)
        
        # Verify first action
        self.assertEqual(resp["actions"][0]["action"], "open_app")
        self.assertEqual(resp["actions"][0]["params"]["app_name"], "chrome")
        
        # Verify second action
        self.assertEqual(resp["actions"][1]["action"], "store_memory")
        self.assertEqual(resp["actions"][1]["params"]["content"], "my exam is on Monday")

    def test_task_planner_internet_dependency(self):
        # Action that does NOT need internet
        actions_offline = [{"action": "open_app", "params": {"app_name": "notepad"}, "response": "Opening Notepad"}]
        plan_offline = self.task_planner.plan_steps(actions_offline)
        # Should contain only 1 step (opening notepad)
        self.assertEqual(len(plan_offline), 1)
        self.assertEqual(plan_offline[0]["action"], "open_app")

        # Action that DOES need internet
        actions_online = [{"action": "open_url", "params": {"url": "google.com"}, "response": "Opening Google"}]
        plan_online = self.task_planner.plan_steps(actions_online)
        # Should contain 2 steps: 1st check_wifi, 2nd open_url
        self.assertEqual(len(plan_online), 2)
        self.assertEqual(plan_online[0]["action"], "check_wifi")
        self.assertEqual(plan_online[1]["action"], "open_url")

    def test_memory_store_habits_and_streaks(self):
        # Add habit
        self.memory_store.add_habit("study ML")
        habits = self.memory_store.get_habits()
        self.assertTrue(any(h[0] == "study ML" for h in habits))

        # Log first study activity
        streak1 = self.memory_store.log_habit_activity("study ML")
        self.assertEqual(streak1, 1)

    def test_reflection_suggestions(self):
        # Seed a goal
        g_id = self.db.add_goal("Become top AIML student")
        # No recent activity on ML/AIML keyword, should yield a proactive suggestion
        suggestions = self.reflection.generate_reflection_suggestions()
        self.assertTrue(len(suggestions) > 0)
        self.assertTrue("Become top AIML student" in suggestions[0])

if __name__ == "__main__":
    unittest.main()
