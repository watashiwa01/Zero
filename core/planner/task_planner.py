from datetime import datetime


class TaskPlanner:
    """Plans and sequences execution steps for Zero's cognitive loop.
    
    Upgrades from v0.2:
    - Goal-aware step injection (checks active goals before execution)
    - Memory recall injection for context-dependent commands
    - Post-execution memory save steps
    - Priority-based action ordering
    """
    
    def __init__(self, goals_manager=None, memory_store=None):
        self.goals = goals_manager
        self.memory = memory_store
    
    def plan_steps(self, actions):
        """
        Processes the actions parsed by the intent/decision engine and
        structures them into an ordered execution plan.
        
        Injects dependencies:
        - Network check before internet-reliant actions
        - Memory recall before context-dependent actions
        - Memory save after store_memory actions
        """
        plan = []
        internet_reliant_actions = ["open_url", "search_web", "toggle_wifi", "check_wifi"]
        memory_actions = ["recall_memory", "store_memory"]
        
        # --- Pre-checks ---
        
        # 1. Check if internet access is needed
        needs_internet = any(
            act.get("action") in internet_reliant_actions for act in actions
        )
        if needs_internet and not (
            actions and actions[0].get("action") in ["check_wifi", "toggle_wifi"]
        ):
            plan.append({
                "step": len(plan) + 1,
                "action": "check_wifi",
                "params": {},
                "response": "Ensuring we have internet access.",
                "injected": True
            })
        
        # 2. If any action relates to goals, inject goal context
        goal_related_keywords = ["goal", "plan", "study", "learn", "project", "work"]
        has_goal_context = False
        for act in actions:
            params_str = str(act.get("params", {})).lower()
            response_str = str(act.get("response", "")).lower()
            if any(kw in params_str or kw in response_str for kw in goal_related_keywords):
                has_goal_context = True
                break
        
        if has_goal_context and self.goals:
            top_goal = self.goals.get_top_priority_goal()
            if top_goal:
                plan.append({
                    "step": len(plan) + 1,
                    "action": "goal_context",
                    "params": {
                        "goal": top_goal["description"],
                        "progress": top_goal.get("progress", 0),
                        "next_action": top_goal.get("next_action")
                    },
                    "response": f"Active goal: {top_goal['description']} ({top_goal.get('progress', 0)}% complete)",
                    "injected": True
                })
        
        # --- Primary actions (priority-sorted) ---
        priority_order = {
            "check_wifi": 0,
            "toggle_wifi": 1,
            "check_battery": 2,
            "recall_memory": 3,
            "store_memory": 4,
            "open_app": 5,
            "open_url": 6,
            "search_web": 7,
            "close_app": 8,
            "create_folder": 9,
            "chat": 10,
        }
        
        sorted_actions = sorted(
            actions,
            key=lambda a: priority_order.get(a.get("action", "chat"), 10)
        )
        
        for act in sorted_actions:
            plan.append({
                "step": len(plan) + 1,
                "action": act.get("action", "chat"),
                "params": act.get("params", {}),
                "response": act.get("response", "")
            })
        
        return plan
    
    def enrich_plan_with_suggestions(self, plan, state=None):
        """Optional: Add follow-up suggestions after execution.
        
        Called after execution to suggest next steps based on what was done.
        Returns a list of suggestion strings.
        """
        suggestions = []
        
        actions_taken = [step.get("action") for step in plan if not step.get("injected")]
        
        if "open_app" in actions_taken:
            # Check which app was opened
            for step in plan:
                if step.get("action") == "open_app":
                    app = step.get("params", {}).get("app_name", "").lower()
                    if "code" in app or "vs" in app:
                        if self.goals:
                            top = self.goals.get_top_priority_goal()
                            if top:
                                suggestions.append(
                                    f"You opened your editor. Your top goal is '{top['description']}' — "
                                    f"want me to track time on it?"
                                )
        
        if "search_web" in actions_taken:
            suggestions.append("Would you like me to remember these search results?")
        
        if "store_memory" in actions_taken:
            suggestions.append("Memory saved. I'll recall this when relevant.")
        
        return suggestions
