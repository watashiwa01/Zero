from datetime import datetime, timedelta

class PlannerManager:
    def __init__(self, db_manager):
        self.db = db_manager

    def generate_proactive_suggestions(self):
        """
        Inspects goals and tasks, and returns autonomous recommendations 
        if there has been lack of recent progress on any goals.
        """
        suggestions = []
        goals = self.db.get_goals()
        
        if not goals:
            return suggestions

        memories = self.db.recall_memories()
        
        for goal in goals:
            g_id, g_desc, g_date, g_status = goal
            if g_status != 'completed':
                keywords = [word.lower() for word in g_desc.split() if len(word) > 3]
                
                has_recent_activity = False
                for m_content, m_time, m_cat in memories:
                    try:
                        m_dt = datetime.strptime(m_time, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        try:
                            m_dt = datetime.strptime(m_time.split('.')[0], "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            m_dt = datetime.now()

                    if datetime.now() - m_dt < timedelta(days=4):
                        if any(kw in m_content.lower() for kw in keywords):
                            has_recent_activity = True
                            break
                
                if not has_recent_activity:
                    suggestions.append(
                        f"You haven't logged activity for your goal '{g_desc}' recently. "
                        "Would you like to schedule a 30-minute revision or focus session?"
                    )
        
        return suggestions
