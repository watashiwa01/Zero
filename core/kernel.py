import os
import psutil
from core.memory import DatabaseManager
from core.memory.memory_store import MemoryStore
from core.brain.intent_engine import IntentEngine
from core.brain.personality import PersonalityManager
from core.planner.task_planner import TaskPlanner
from core.system.network_monitor import NetworkMonitor
from core.reflection.reflection_engine import ReflectionEngine
from core.goals import GoalsManager
from agents.system import SystemAgent
from agents.voice import VoiceAgent
from agents.browser import BrowserAgent

class ZeroKernel:
    def __init__(self):
        # Database & Core Storage
        self.db = DatabaseManager()
        self.memory_store = MemoryStore(self.db)
        
        # Upgraded Intelligence Modules
        self.intent_engine = IntentEngine()
        self.task_planner = TaskPlanner()
        self.network = NetworkMonitor()
        self.reflection = ReflectionEngine(self.memory_store)
        self.personality = PersonalityManager()
        
        # System & Agent Controllers
        self.system = SystemAgent()
        self.voice = VoiceAgent()
        self.browser = BrowserAgent()
        self.goals_mgr = GoalsManager(self.db)
        self.session_id = "default_session"
        self.last_suggestion = None  # Tracks active suggestion context
        
        # Populate defaults on startup if empty
        self._bootstrap_default_goals()

    def _bootstrap_default_goals(self):
        goals = self.db.get_goals()
        if not goals:
            g1_id = self.db.add_goal("Become top AIML student")
            self.db.add_task("Finish DSA Sheet", goal_id=g1_id)
            self.memory_store.save_preference("learning_style", "project based learning")
            
            g2_id = self.db.add_goal("Crack AI900")
            self.db.add_task("Review AI900 study guide", goal_id=g2_id)
            
            # Setup default habits to track
            self.memory_store.add_habit("study ML")
            self.memory_store.add_habit("workout")

    def handle_command(self, user_input):
        user_input_clean = user_input.strip()
        if not user_input_clean:
            return "I didn't hear anything."

        # 1. Parse user intent (Ollama or Fallback)
        intent_response = self.intent_engine.process_input(user_input_clean)
        actions = intent_response.get("actions", [])
        base_reply = intent_response.get("response", "")

        # 2. Check if the intent is a conversational response to a pending suggestion or general chat
        if len(actions) == 1 and actions[0].get("action") in ["affirmation", "greeting", "gratitude", "chat"]:
            conv_action = actions[0].get("action")
            params = actions[0].get("params", {})
            
            if conv_action == "affirmation":
                val = params.get("value", True)
                if self.last_suggestion:
                    sugg = self.last_suggestion
                    self.last_suggestion = None  # Clear suggestion
                    
                    if val:
                        # Log the suggested habit
                        if "habit" in sugg:
                            self.memory_store.log_habit_activity(sugg["habit"])
                        
                        # Run the suggestion's target action
                        res = None
                        if sugg.get("action") == "open_app":
                            res = self.system.open_app(sugg["params"].get("app_name", ""))
                        elif sugg.get("action") == "search_web":
                            res = self.browser.search_google(sugg["params"].get("query", ""))
                        elif sugg.get("action") == "store_memory":
                            res = f"Stored memory: \"{sugg['params'].get('content', '')}\""
                            self.db.save_memory(sugg["params"].get("content", ""))
                            
                        outcome = res if res else "Suggestion executed."
                        final_res = f"Awesome, Varun! I've logged your study activity and started that for you: {outcome}"
                    else:
                        final_res = "No problem, Varun. Let me know when you're ready to focus on it."
                else:
                    final_res = "Alright, Varun."
                    
            elif conv_action == "greeting":
                self.last_suggestion = None
                final_res = "Hello Varun! How can I help you today?"
                
            elif conv_action == "gratitude":
                self.last_suggestion = None
                final_res = "You're very welcome, Varun. Always happy to assist!"
                
            else:  # General chat fallback
                if self.last_suggestion:
                    final_res = f"I'm here, Varun. I had suggested: '{self.last_suggestion['text']}'. What would you like to do?"
                else:
                    final_res = f"I heard you, Varun. What would you like me to open or remember?"
            
            # Save logs and return
            self.db.save_conversation(self.session_id, "user", user_input_clean)
            self.db.save_conversation(self.session_id, "assistant", final_res)
            return final_res

        # If it's a structural command, reset the last suggestion
        self.last_suggestion = None

        # 3. Plan execution sequence
        plan = self.task_planner.plan_steps(actions)

        # 4. Execution Loop
        action_results = []
        last_action_type = None
        last_params = {}
        
        for step in plan:
            action = step.get("action")
            params = step.get("params", {})
            last_action_type = action
            last_params = params
            
            res = None
            if action == "open_app":
                app_name = params.get("app_name", "")
                res = self.system.open_app(app_name)
                if "code" in app_name.lower() or "vs" in app_name.lower():
                    self.memory_store.log_habit_activity("study ML")
                    
            elif action == "close_app":
                app_name = params.get("app_name", "")
                res = self.system.close_app(app_name)
                
            elif action == "open_url":
                url = params.get("url", "")
                res = self.browser.open_url(url)
                
            elif action == "search_web":
                query = params.get("query", "")
                res = self.browser.search_google(query)
                
            elif action == "toggle_wifi":
                state = params.get("state", "on")
                res = self.network.toggle_wifi(state)
                
            elif action == "check_wifi":
                res = self.network.check_wifi()
                
            elif action == "check_battery":
                res = self.system.check_battery()
                
            elif action == "store_memory":
                content = params.get("content", "")
                self.db.save_memory(content)
                res = f"Stored memory: \"{content}\""
                
            elif action == "recall_memory":
                query = params.get("query", "")
                memories = self.db.recall_memories(query)
                if memories:
                    lines = [f"- {m[0]} (saved on {m[1].split(' ')[0]})" for m in memories]
                    res = "Here is what I remember:\n" + "\n".join(lines)
                else:
                    res = f"I couldn't find any memories matching '{query}'."
                    
            elif action == "create_folder":
                folder_path = params.get("folder_path", "")
                res = self.system.create_folder(folder_path)
                
            elif action == "chat":
                res = step.get("response", "")
                
            if res:
                action_results.append(res)

        # 5. Gather execution context for personality enhancement
        context = {}
        try:
            battery = psutil.sensors_battery()
            if battery:
                context["battery_percent"] = battery.percent
                context["power_plugged"] = battery.power_plugged
        except Exception:
            pass
            
        context["internet_status"] = "online" if self.network.check_internet() else "offline"

        # Combine results into final reply
        if action_results:
            if len(action_results) > 1:
                combined_res = "Done. Tasks executed:\n" + "\n".join(f"{i+1}. {r}" for i, r in enumerate(action_results))
            else:
                combined_res = action_results[0]
        else:
            combined_res = base_reply

        # 6. Personality Enhancement
        final_reply = self.personality.enhance_response(
            combined_res,
            action_type=last_action_type,
            params=last_params,
            context=context
        )

        # 7. Save turn logs to DB
        self.db.save_conversation(self.session_id, "user", user_input_clean)
        self.db.save_conversation(self.session_id, "assistant", final_reply)
        
        return final_reply

    def get_proactive_suggestion(self):
        suggestions = self.reflection.generate_reflection_suggestions()
        if suggestions:
            suggestion_text = suggestions[0]
            # Store the suggestion context and map its logical positive outcomes
            self.last_suggestion = {
                "text": suggestion_text,
                "action": "open_app",
                "params": {"app_name": "code"},
                "habit": "study ML"
            }
            if "ai900" in suggestion_text.lower():
                self.last_suggestion["action"] = "search_web"
                self.last_suggestion["params"] = {"query": "Microsoft Azure AI Fundamentals study guide"}
            elif "workout" in suggestion_text.lower():
                self.last_suggestion["action"] = "store_memory"
                self.last_suggestion["params"] = {"content": "Worked out today"}
                self.last_suggestion["habit"] = "workout"
                
            return suggestion_text
        return None
