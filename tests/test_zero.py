import unittest
import os
import sys

# Add root folder to path to import core and agents
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.memory import DatabaseManager
from core.brain import BrainAgent
from agents.system import SystemAgent

class TestZeroOS(unittest.TestCase):
    def setUp(self):
        # Use a temporary test database
        self.db_path = "test_zero.db"
        self.db = DatabaseManager(db_path=self.db_path)
        self.brain = BrainAgent()
        self.system = SystemAgent()

    def tearDown(self):
        # Remove test database file
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except PermissionError:
                pass

    def test_database_creation(self):
        # Verify that the database initialized and tables exist
        self.assertTrue(os.path.exists(self.db_path))

    def test_memory_crud(self):
        # Save a memory
        mem_id = self.db.save_memory("Varun prefers project based learning", category="preference")
        self.assertIsNotNone(mem_id)

        # Recall memories
        results = self.db.recall_memories("learning")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][0], "Varun prefers project based learning")

    def test_brain_fallback(self):
        # Test rule-based intent parsing (fallback)
        resp1 = self.brain._rule_based_fallback("open chrome")
        self.assertEqual(resp1["action"], "open_app")
        self.assertEqual(resp1["params"]["app_name"], "chrome")

        resp2 = self.brain._rule_based_fallback("remember that my ML exam is on Monday")
        self.assertEqual(resp2["action"], "store_memory")
        self.assertEqual(resp2["params"]["content"], "my ML exam is on Monday")

        resp3 = self.brain._rule_based_fallback("check battery")
        self.assertEqual(resp3["action"], "check_battery")

    def test_system_status(self):
        # Test basic system inspection utilities (should run without raising errors)
        battery_status = self.system.check_battery()
        self.assertIsInstance(battery_status, str)
        self.assertTrue(len(battery_status) > 0)

        wifi_status = self.system.check_wifi()
        self.assertIsInstance(wifi_status, str)
        self.assertTrue(len(wifi_status) > 0)

if __name__ == "__main__":
    unittest.main()
