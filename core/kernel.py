import os
from core.memory import DatabaseManager
from core.brain import BrainAgent
from core.goals import GoalsManager
from core.planner import PlannerManager
from agents.system import SystemAgent
from agents.voice import VoiceAgent
from agents.browser import BrowserAgent

class ZeroKernel:
    def __init__(self):
        self.db = DatabaseManager()
        self.brain = BrainAgent()
        self.system = SystemAgent()
        self.voice = VoiceAgent()
        self.browser = BrowserAgent()
        self.goals_mgr = GoalsManager(self.db)
        self.planner = PlannerManager(self.db)
        self.session_id = "default_session"
        
        # Populate defaults on startup if empty
        self._bootstrap_default_goals()

    def _bootstrap_default_goals(self):
        # Check if goals table is empty, and populate the defaults from the prompt
        goals = self.db.get_goals()
        if not goals:
            # Goal 1: Become top AIML student
            g1_id = self.db.add_goal("Become top AIML student")
            self.db.add_task("Finish DSA Sheet", goal_id=g1_id)
            self.db.save_memory("Varun prefers project based learning", category="preferences")
            
            # Goal 2: Crack AI900
            g2_id = self.db.add_goal("Crack AI900")
            self.db.add_task("Review AI900 study guide", goal_id=g2_id)

    def handle_command(self, user_input):
        user_input_clean = user_input.strip()
        if not user_input_clean:
            return "I didn't hear anything."

        # Parse user intent through Brain
        brain_response = self.brain.process_input(user_input_clean)
        action = brain_response.get("action")
        params = brain_response.get("params", {})
        conversational_reply = brain_response.get("response", "")

        # Execute system action based on parsed intent
        action_result = None
        
        if action == "open_app":
            app_name = params.get("app_name", "")
            action_result = self.system.open_app(app_name)
            
        elif action == "close_app":
            app_name = params.get("app_name", "")
            action_result = self.system.close_app(app_name)
            
        elif action == "store_memory":
            content = params.get("content", "")
            self.db.save_memory(content)
            action_result = f"I have stored that memory: \"{content}\""
            
        elif action == "recall_memory":
            query = params.get("query", "")
            memories = self.db.recall_memories(query)
            if memories:
                memory_lines = [f"- {m[0]} (saved on {m[1].split(' ')[0]})" for m in memories]
                action_result = "Here is what I remember:\n" + "\n".join(memory_lines)
            else:
                action_result = "I couldn't find any memories matching that query."
                
        elif action == "check_battery":
            action_result = self.system.check_battery()
            
        elif action == "check_wifi":
            action_result = self.system.check_wifi()
            
        elif action == "create_folder":
            folder_path = params.get("folder_path", "")
            action_result = self.system.create_folder(folder_path)

        # Log conversation turns
        self.db.save_conversation(self.session_id, "user", user_input_clean)
        final_reply = action_result if action_result else conversational_reply
        self.db.save_conversation(self.session_id, "assistant", final_reply)
        
        return final_reply

    def get_proactive_suggestion(self):
        suggestions = self.planner.generate_proactive_suggestions()
        if suggestions:
            return suggestions[0]  # Return the top suggestion
        return None
