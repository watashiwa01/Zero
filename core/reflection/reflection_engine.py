from datetime import datetime, timedelta

class ReflectionEngine:
    def __init__(self, memory_store):
        self.memory_store = memory_store

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
            g_id, g_desc, g_date, g_status = goal
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
