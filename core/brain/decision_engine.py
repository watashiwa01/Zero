import re
from datetime import datetime


class DecisionEngine:
    """Zero's cognitive decision layer.
    
    Sits between user input and the intent engine.
    Handles 'thinking' questions (what should I do, continue where we left, etc.)
    by analyzing goals, memory, and recent activity.
    For direct commands, delegates to the intent engine.
    """
    
    def __init__(self, intent_engine, memory_store, goals_manager, state):
        self.intent = intent_engine
        self.memory = memory_store
        self.goals = goals_manager
        self.state = state
        
        # Patterns that trigger the decision engine instead of intent engine
        self._thinking_patterns = [
            r"what should i (do|work on|focus on)",
            r"what('s| is) (next|my priority|important)",
            r"i have (\d+)\s*(hour|minute|min|hr)",
            r"continue where (we|i) left",
            r"what (did|was) i (doing|working on)",
            r"suggest something",
            r"help me (plan|decide|prioritize)",
            r"what are my goals",
            r"how am i doing",
            r"give me a (plan|schedule|breakdown)",
            r"status report",
        ]
    
    def process(self, user_input):
        """Main entry point. Decides whether to think or delegate.
        
        Returns dict with:
        - 'type': 'decision' or 'command'
        - 'response': text response for decisions
        - 'actions': list of actions for commands
        - 'intent': intent classification
        """
        text_lower = user_input.strip().lower()
        
        # Check if this is a thinking question
        for pattern in self._thinking_patterns:
            if re.search(pattern, text_lower):
                return self._handle_thinking(user_input, text_lower, pattern)
        
        # Otherwise delegate to intent engine
        intent_result = self.intent.process_input(user_input)
        return {
            "type": "command",
            "intent": intent_result.get("intent", "single_action"),
            "actions": intent_result.get("actions", []),
            "response": intent_result.get("response", "")
        }
    
    def _handle_thinking(self, original_input, text_lower, matched_pattern):
        """Handle questions that require Zero to think and reason."""
        
        # "What should I do?" / "What's next?" / "Suggest something"
        if re.search(r"what should i|what('s| is) (next|my priority)|suggest|help me (plan|decide|prioritize)", text_lower):
            return self._recommend_next_action()
        
        # "I have X hours/minutes free"
        time_match = re.search(r"i have (\d+)\s*(hour|minute|min|hr)s?", text_lower)
        if time_match:
            amount = int(time_match.group(1))
            unit = time_match.group(2)
            minutes = amount * 60 if unit in ["hour", "hr"] else amount
            return self._plan_time_block(minutes)
        
        # "Continue where we left" / "What was I doing?"
        if re.search(r"continue where|what (did|was) i (doing|working)", text_lower):
            return self._resume_context()
        
        # "What are my goals?" / "Status report" / "How am I doing?"
        if re.search(r"what are my goals|status report|how am i doing", text_lower):
            return self._generate_status_report()
        
        # Fallback — still a thinking question but unmatched sub-type
        return self._recommend_next_action()
    
    def _recommend_next_action(self):
        """Analyze goals and activity to recommend what to do."""
        recommendations = self.goals.get_daily_recommendation()
        
        if not recommendations:
            return {
                "type": "decision",
                "intent": "recommendation",
                "actions": [],
                "response": (
                    "Varun, all your goals are on track! "
                    "You could start a new project, revise something, or take a well-earned break."
                )
            }
        
        lines = ["Varun, here's what I recommend based on your goals:\n"]
        for i, rec in enumerate(recommendations[:3], 1):
            priority_tag = f"[{rec['priority'].upper()}]" if rec['priority'] == 'high' else f"[{rec['priority']}]"
            reason = "(neglected)" if rec['reason'] == 'neglected' else "(top priority)"
            lines.append(f"{i}. {priority_tag} {rec['suggestion']} {reason}")
        
        top = recommendations[0]
        lines.append(f"\nI suggest starting with: {top['suggestion']}")
        lines.append("Shall I help you get started?")
        
        return {
            "type": "decision",
            "intent": "recommendation",
            "actions": [],
            "response": "\n".join(lines)
        }
    
    def _plan_time_block(self, total_minutes):
        """Create a time-blocked plan based on available time."""
        recommendations = self.goals.get_daily_recommendation()
        
        if not recommendations:
            return {
                "type": "decision",
                "intent": "time_plan",
                "actions": [],
                "response": (
                    f"Varun, you have {total_minutes} minutes free. "
                    "All goals are on track — use this time for exploration or rest."
                )
            }
        
        # Allocate time proportionally based on number of recommendations
        plan_lines = [f"Varun, here's your {total_minutes}-minute plan:\n"]
        
        if total_minutes >= 60 and len(recommendations) >= 2:
            # Split time: 60% to top priority, 40% to second
            primary_time = int(total_minutes * 0.6)
            secondary_time = total_minutes - primary_time
            
            plan_lines.append(f"1. {recommendations[0]['suggestion']} — {primary_time} min")
            plan_lines.append(f"2. {recommendations[1]['suggestion']} — {secondary_time} min")
        elif total_minutes >= 30:
            plan_lines.append(f"1. {recommendations[0]['suggestion']} — {total_minutes} min")
        else:
            plan_lines.append(f"Quick focus: {recommendations[0]['suggestion']} — {total_minutes} min")
        
        plan_lines.append("\nShall I start a timer or open anything for you?")
        
        return {
            "type": "decision",
            "intent": "time_plan",
            "actions": [],
            "response": "\n".join(plan_lines)
        }
    
    def _resume_context(self):
        """Load last session context and offer to continue."""
        continuity = self.memory.get_continuity_summary()
        
        if not continuity:
            return {
                "type": "decision",
                "intent": "resume",
                "actions": [],
                "response": (
                    "Varun, this looks like your first session — I don't have previous context yet. "
                    "What would you like to work on?"
                )
            }
        
        lines = ["Varun, here's where we left off:\n"]
        
        if continuity.get("summary"):
            lines.append(f"Last session: {continuity['summary']}")
        
        context = continuity.get("context", {})
        if context.get("last_command"):
            lines.append(f"Last command: {context['last_command']}")
        if context.get("active_goal"):
            lines.append(f"Active goal: {context['active_goal']}")
        if context.get("current_task"):
            lines.append(f"Working on: {context['current_task']}")
        if context.get("commands_processed"):
            lines.append(f"Commands last session: {context['commands_processed']}")
        
        lines.append("\nWould you like to continue from here?")
        
        return {
            "type": "decision",
            "intent": "resume",
            "actions": [],
            "response": "\n".join(lines)
        }
    
    def _generate_status_report(self):
        """Generate a comprehensive status report."""
        report = self.goals.get_goal_status_report()
        habits = self.memory.get_habits()
        
        lines = ["Varun, here's your status report:\n"]
        
        # Goals
        lines.append("═══ GOALS ═══")
        if report:
            for g in report:
                status_icon = "✅" if g['status'] == 'completed' else "🔄"
                priority_tag = f"[{g.get('priority', 'medium').upper()}]" if g.get('priority') == 'high' else ""
                progress = g.get('progress', 0)
                bar_filled = int(progress / 10)
                bar_empty = 10 - bar_filled
                progress_bar = f"[{'█' * bar_filled}{'░' * bar_empty}] {progress}%"
                lines.append(f"{status_icon} {priority_tag} {g['description']}")
                lines.append(f"   {progress_bar}  Tasks: {g.get('task_progress', 'N/A')}")
                if g.get('next_action'):
                    lines.append(f"   Next: {g['next_action']}")
        else:
            lines.append("No goals set yet.")
        
        # Habits
        lines.append("\n═══ HABITS ═══")
        if habits:
            for name, last_logged, streak in habits:
                streak_display = f"🔥 {streak} day streak" if streak and streak > 0 else "Not started"
                lines.append(f"• {name}: {streak_display}")
        else:
            lines.append("No habits tracked yet.")
        
        # Session info
        duration = self.state.get_session_duration_minutes()
        lines.append(f"\n═══ SESSION ═══")
        lines.append(f"Duration: {duration} min | Commands: {self.state.commands_this_session}")
        
        return {
            "type": "decision",
            "intent": "status_report",
            "actions": [],
            "response": "\n".join(lines)
        }
