from datetime import datetime, timedelta


class ReflectionEngine:
    def __init__(self, memory_store, goals_manager=None, state=None):
        self.memory_store = memory_store
        self.goals = goals_manager
        self.state = state

    def generate_startup_briefing(self):
        """Generate a personalized greeting with context from last session."""
        hour = datetime.now().hour
        if hour < 12:
            greeting = "Good morning"
        elif hour < 17:
            greeting = "Good afternoon"
        else:
            greeting = "Good evening"
        
        lines = [f"{greeting}, Varun.\n"]
        
        # Last session context
        continuity = self.memory_store.get_continuity_summary()
        if continuity:
            if continuity.get("summary"):
                lines.append(f"Last session: {continuity['summary']}")
            context = continuity.get("context", {})
            if context.get("active_goal"):
                lines.append(f"You were working on: {context['active_goal']}")
            if context.get("current_task"):
                lines.append(f"Task in progress: {context['current_task']}")
            lines.append("")
        
        # Goal-based suggestions
        if self.goals:
            neglected = self.goals.get_neglected_goals(days=2)
            if neglected:
                top = neglected[0]
                lines.append(f"⚠ Your goal '{top['description']}' needs attention.")
                if top.get('next_action'):
                    lines.append(f"   Suggested: {top['next_action']}")
                lines.append("")
            
            top_goal = self.goals.get_top_priority_goal()
            if top_goal and (not neglected or top_goal['description'] != neglected[0]['description']):
                lines.append(f"Top priority: {top_goal['description']} ({top_goal.get('progress', 0)}% complete)")
                lines.append("")
        
        # Habit check
        habits = self.memory_store.get_habits()
        pending_habits = []
        for name, last_logged, streak in habits:
            if last_logged:
                try:
                    last_dt = datetime.strptime(last_logged, "%Y-%m-%d %H:%M:%S")
                    if (datetime.now().date() - last_dt.date()).days >= 1:
                        pending_habits.append((name, streak))
                except ValueError:
                    pending_habits.append((name, streak))
            else:
                pending_habits.append((name, 0))
        
        if pending_habits:
            lines.append("Pending habits today:")
            for name, streak in pending_habits:
                streak_info = f" (🔥 {streak} day streak)" if streak and streak > 0 else ""
                lines.append(f"  • {name}{streak_info}")
            lines.append("")
        
        lines.append("What would you like to work on?")
        
        return "\n".join(lines)

    def generate_reflection_suggestions(self):
        """
        Reflects on goals, tasks, recent conversations, and habits.
        Generates insights, reminders, or proactive study focus warnings for Varun.
        """
        suggestions = []
        db = self.memory_store.db
        
        # 1. Check goal activity
        goals = db.get_goals()
        memories = db.recall_memories()
        
        for goal in goals:
            g_id, g_desc, g_date, g_status = goal[:4]
            if g_status != 'completed':
                # Extract descriptive keywords (exclude short pronouns/prepositions)
                keywords = [w.lower() for w in g_desc.split() if len(w) > 3]
                
                # Check for matching recent memory
                has_recent_activity = False
                for m_content, m_time, m_cat in memories:
                    try:
                        m_dt = datetime.strptime(m_time.split('.')[0], "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        m_dt = datetime.now()
                        
                    # Consider active if logged within 4 days and matching keywords
                    if datetime.now() - m_dt < timedelta(days=4):
                        if any(kw in m_content.lower() for kw in keywords):
                            has_recent_activity = True
                            break
                            
                if not has_recent_activity:
                    suggestions.append(
                        f"You haven't logged activity for your goal '{g_desc}' recently. "
                        f"Would you like to schedule some time to focus on this, Varun?"
                    )

        # 2. Check habits
        habits = self.memory_store.get_habits()
        for name, last_logged, streak in habits:
            if last_logged:
                try:
                    last_dt = datetime.strptime(last_logged, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    last_dt = datetime.now()
                
                delta_days = (datetime.now().date() - last_dt.date()).days
                if delta_days >= 1:
                    suggestions.append(
                        f"Your streak for the habit '{name}' is at {streak} days, but you haven't logged it today. "
                        f"Shall we get to work on it?"
                    )
            else:
                suggestions.append(f"You have a pending habit '{name}' that hasn't been started. Would you like to log it?")

        return suggestions

    def generate_session_wrapup(self):
        """Generate a summary when Zero is shutting down."""
        lines = ["\nSession wrapup, Varun:\n"]
        
        if self.state:
            duration = self.state.get_session_duration_minutes()
            lines.append(f"Session duration: {duration} minutes")
            lines.append(f"Commands processed: {self.state.commands_this_session}")
            if self.state.last_command:
                lines.append(f"Last command: {self.state.last_command}")
            if self.state.active_goal:
                lines.append(f"Active goal: {self.state.active_goal}")
        
        lines.append("\nGoodbye, Varun. I'll remember where we left off.")
        return "\n".join(lines)

