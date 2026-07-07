import os
import psutil
from core.memory import DatabaseManager
from core.memory.memory_store import MemoryStore
from core.brain.intent_engine import IntentEngine
from core.brain.decision_engine import DecisionEngine
from core.brain.personality import PersonalityManager
from core.planner.task_planner import TaskPlanner
from core.system.network_monitor import NetworkMonitor
from core.reflection.reflection_engine import ReflectionEngine
from core.goals import GoalsManager
from core.state.zero_state import ZeroState
from agents.system import SystemAgent
from agents.voice import VoiceAgent
from agents.browser import BrowserAgent


class ZeroKernel:
    """Zero OS Kernel v0.3 — Intelligence Upgrade.
    
    Cognitive loop:
        Input → Short-term Memory → Decision Engine → Memory Recall →
        Goal Analysis → Planner → Agent Execution → Reflection →
        Memory Update → State Update → Personality → Reply
    """
    
    def __init__(self):
        # ── Database & Core Storage ──
        self.db = DatabaseManager()
        self.memory_store = MemoryStore(self.db)
        
        # ── State Tracking ──
        self.state = ZeroState()
        
        # ── Intelligence Modules ──
        self.intent_engine = IntentEngine()
        self.personality = PersonalityManager()
        self.network = NetworkMonitor()
        
        # ── Goal-aware modules (need db) ──
        self.goals_mgr = GoalsManager(self.db)
        
        # ── Planner (now goal-aware) ──
        self.task_planner = TaskPlanner(
            goals_manager=self.goals_mgr,
            memory_store=self.memory_store
        )
        
        # ── Decision Engine (wraps intent engine) ──
        self.decision_engine = DecisionEngine(
            intent_engine=self.intent_engine,
            memory_store=self.memory_store,
            goals_manager=self.goals_mgr,
            state=self.state
        )
        
        # ── Reflection (now goal + state aware) ──
        self.reflection = ReflectionEngine(
            self.memory_store,
            goals_manager=self.goals_mgr,
            state=self.state
        )
        
        # ── System & Agent Controllers ──
        self.system = SystemAgent()
        self.voice = VoiceAgent()
        self.browser = BrowserAgent()
        
        self.last_suggestion = None  # Tracks active suggestion context
        
        # ── Session Startup ──
        self.memory_store.start_session(self.state.session_id)
        self._bootstrap_default_goals()

    def _bootstrap_default_goals(self):
        """Populate default goals and habits on first run."""
        goals = self.db.get_goals()
        if not goals:
            g1_id = self.db.add_goal("Become top AIML student")
            self.db.update_goal_priority(g1_id, "high")
            self.db.add_task("Finish DSA Sheet", goal_id=g1_id)
            self.memory_store.save_preference("learning_style", "project based learning")
            
            g2_id = self.db.add_goal("Crack AI900")
            self.db.add_task("Review AI900 study guide", goal_id=g2_id)
            
            # Setup default habits to track
            self.memory_store.add_habit("study ML")
            self.memory_store.add_habit("workout")

    # ═══════════════════════════════════════════════════════
    #  MAIN COGNITIVE LOOP
    # ═══════════════════════════════════════════════════════

    def handle_command(self, user_input):
        """Process user input through Zero's cognitive loop.
        
        Flow:
        1. Save to short-term memory
        2. Decision Engine (think or delegate)
        3. For decisions: return response directly
        4. For commands: plan → execute → reflect → respond
        5. Update state and memory
        """
        user_input_clean = user_input.strip()
        if not user_input_clean:
            return "I didn't hear anything."

        # ── Step 1: Save to short-term memory ──
        self.memory_store.push_turn("user", user_input_clean)

        # ── Step 2: Decision Engine ──
        decision = self.decision_engine.process(user_input_clean)

        # ── Step 3: Handle "thinking" decisions ──
        if decision["type"] == "decision":
            response = decision["response"]
            
            # Apply personality
            final_reply = self.personality.enhance_response(
                response,
                action_type="decision",
                params={},
                context={}
            )
            
            # Save to memory and state
            self.memory_store.push_turn("assistant", final_reply)
            self.db.save_conversation(self.state.session_id, "user", user_input_clean)
            self.db.save_conversation(self.state.session_id, "assistant", final_reply)
            self.state.record_command(user_input_clean, action_type=decision.get("intent"))
            
            return final_reply

        # ── Step 4: Handle command flow ──
        actions = decision.get("actions", [])
        base_reply = decision.get("response", "")

        # Check for conversational intents (affirmation, greeting, gratitude, chat)
        if len(actions) == 1 and actions[0].get("action") in ["affirmation", "greeting", "gratitude", "chat"]:
            final_res = self._handle_conversational(actions[0], user_input_clean)
            
            self.memory_store.push_turn("assistant", final_res)
            self.db.save_conversation(self.state.session_id, "user", user_input_clean)
            self.db.save_conversation(self.state.session_id, "assistant", final_res)
            self.state.record_command(user_input_clean, action_type=actions[0].get("action"))
            return final_res

        # Reset suggestion context for structural commands
        self.last_suggestion = None

        # ── Step 5: Plan execution ──
        plan = self.task_planner.plan_steps(actions)

        # ── Step 6: Execute ──
        action_results = []
        last_action_type = None
        last_params = {}
        
        for step in plan:
            action = step.get("action")
            params = step.get("params", {})
            
            # Skip injected informational steps
            if step.get("injected") and action == "goal_context":
                continue
            
            last_action_type = action
            last_params = params
            
            res = self._execute_action(action, params)
            if res:
                action_results.append(res)

        # ── Step 7: Gather context for personality ──
        context = self._get_system_context()

        # Combine results
        if action_results:
            if len(action_results) > 1:
                combined_res = "Done. Tasks executed:\n" + "\n".join(
                    f"{i+1}. {r}" for i, r in enumerate(action_results)
                )
            else:
                combined_res = action_results[0]
        else:
            combined_res = base_reply

        # ── Step 8: Personality Enhancement ──
        final_reply = self.personality.enhance_response(
            combined_res,
            action_type=last_action_type,
            params=last_params,
            context=context
        )

        # ── Step 9: Update memory and state ──
        self.memory_store.push_turn("assistant", final_reply)
        self.db.save_conversation(self.state.session_id, "user", user_input_clean)
        self.db.save_conversation(self.state.session_id, "assistant", final_reply)
        self.state.record_command(user_input_clean, action_type=last_action_type)
        
        # Track goal-related activity
        if last_action_type in ["open_app", "search_web", "store_memory"]:
            top_goal = self.goals_mgr.get_top_priority_goal()
            if top_goal:
                self.state.set_active_goal(top_goal["description"])

        return final_reply

    # ═══════════════════════════════════════════════════════
    #  CONVERSATIONAL HANDLER
    # ═══════════════════════════════════════════════════════

    def _handle_conversational(self, action_data, user_input_clean):
        """Handle conversational intents: affirmation, greeting, gratitude, chat."""
        conv_action = action_data.get("action")
        params = action_data.get("params", {})
        
        if conv_action == "affirmation":
            val = params.get("value", True)
            if self.last_suggestion:
                sugg = self.last_suggestion
                self.last_suggestion = None
                
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
                    return f"Awesome, Varun! I've logged your activity and started that for you: {outcome}"
                else:
                    return "No problem, Varun. Let me know when you're ready to focus on it."
            else:
                return "Alright, Varun."
                
        elif conv_action == "greeting":
            self.last_suggestion = None
            return "Hello Varun! How can I help you today?"
            
        elif conv_action == "gratitude":
            self.last_suggestion = None
            return "You're very welcome, Varun. Always happy to assist!"
            
        else:  # General chat fallback
            if self.last_suggestion:
                return f"I'm here, Varun. I had suggested: '{self.last_suggestion['text']}'. What would you like to do?"
            else:
                return "I heard you, Varun. What would you like me to open or remember?"

    # ═══════════════════════════════════════════════════════
    #  ACTION EXECUTOR
    # ═══════════════════════════════════════════════════════

    def _execute_action(self, action, params):
        """Execute a single action and return result string."""
        if action == "open_app":
            app_name = params.get("app_name", "")
            res = self.system.open_app(app_name)
            if "code" in app_name.lower() or "vs" in app_name.lower():
                self.memory_store.log_habit_activity("study ML")
                self.state.set_current_task("Coding")
            return res
                
        elif action == "close_app":
            return self.system.close_app(params.get("app_name", ""))
            
        elif action == "open_url":
            return self.browser.open_url(params.get("url", ""))
            
        elif action == "search_web":
            return self.browser.search_google(params.get("query", ""))
            
        elif action == "toggle_wifi":
            return self.network.toggle_wifi(params.get("state", "on"))
            
        elif action == "check_wifi":
            return self.network.check_wifi()
            
        elif action == "check_battery":
            return self.system.check_battery()
            
        elif action == "store_memory":
            content = params.get("content", "")
            self.db.save_memory(content)
            self.memory_store.save_fact("user_note", content, category="notes")
            return f"Stored memory: \"{content}\""
            
        elif action == "recall_memory":
            query = params.get("query", "")
            memories = self.db.recall_memories(query)
            if memories:
                lines = [f"- {m[0]} (saved on {m[1].split(' ')[0]})" for m in memories]
                return "Here is what I remember:\n" + "\n".join(lines)
            else:
                return f"I couldn't find any memories matching '{query}'."
                
        elif action == "create_folder":
            return self.system.create_folder(params.get("folder_path", ""))
            
        elif action == "chat":
            return params.get("response", "")
        
        return None

    # ═══════════════════════════════════════════════════════
    #  SYSTEM CONTEXT
    # ═══════════════════════════════════════════════════════

    def _get_system_context(self):
        """Gather system context for personality enhancement."""
        context = {}
        try:
            battery = psutil.sensors_battery()
            if battery:
                context["battery_percent"] = battery.percent
                context["power_plugged"] = battery.power_plugged
        except Exception:
            pass
            
        context["internet_status"] = "online" if self.network.check_internet() else "offline"
        return context

    # ═══════════════════════════════════════════════════════
    #  PROACTIVE FEATURES
    # ═══════════════════════════════════════════════════════

    def get_startup_briefing(self):
        """Generate the startup briefing using reflection engine."""
        return self.reflection.generate_startup_briefing()

    def get_proactive_suggestion(self):
        """Generate a proactive suggestion (legacy + upgraded)."""
        suggestions = self.reflection.generate_reflection_suggestions()
        if suggestions:
            suggestion_text = suggestions[0]
            # Store the suggestion context
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

    def shutdown(self):
        """Clean shutdown: save session context, generate wrapup."""
        # Save session context
        snapshot = self.state.get_snapshot()
        self.memory_store.save_session_context(snapshot)
        
        # Generate wrapup
        wrapup = self.reflection.generate_session_wrapup()
        return wrapup
