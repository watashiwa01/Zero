from datetime import datetime, timedelta


class GoalsManager:
    """Manages goals and tasks for Zero OS.
    
    Provides goal creation, status reporting, priority tracking,
    neglect detection, and daily action recommendations.
    """

    def __init__(self, db_manager):
        self.db = db_manager

    def create_goal_with_tasks(self, description, tasks_list=None, target_date=None, priority="medium"):
        """Create a goal with optional tasks. Now supports priority."""
        goal_id = self.db.add_goal(description, target_date)
        if priority != "medium":
            self.db.update_goal_priority(goal_id, priority)
        created_tasks = []
        if tasks_list:
            for task_title in tasks_list:
                task_id = self.db.add_task(task_title, goal_id=goal_id)
                created_tasks.append((task_id, task_title))
        return goal_id, created_tasks

    def get_goal_status_report(self):
        """Enhanced report with priority and progress."""
        goals = self.db.get_goals()
        tasks = self.db.get_tasks()

        report = []
        for g in goals:
            g_id, g_desc, g_date, g_status = g[:4]
            # New fields may exist from ALTER TABLE
            g_priority = g[4] if len(g) > 4 else "medium"
            g_progress = g[5] if len(g) > 5 else 0
            g_next = g[6] if len(g) > 6 else None

            g_tasks = [t for t in tasks if t[4] == g_id]
            completed = sum(1 for t in g_tasks if t[2] == 'completed')
            total = len(g_tasks)

            report.append({
                "id": g_id,
                "description": g_desc,
                "target_date": g_date,
                "status": g_status,
                "priority": g_priority,
                "progress": g_progress,
                "next_action": g_next,
                "task_progress": f"{completed}/{total}" if total > 0 else "No tasks"
            })
        return report

    def get_top_priority_goal(self):
        """Returns the most urgent incomplete goal."""
        report = self.get_goal_status_report()
        active = [g for g in report if g["status"] != "completed"]
        if not active:
            return None

        priority_order = {"high": 0, "medium": 1, "low": 2}
        active.sort(key=lambda g: (priority_order.get(g["priority"], 1), -g["progress"]))
        return active[0]

    def get_neglected_goals(self, days=3):
        """Find goals with no recent activity in the last N days."""
        report = self.get_goal_status_report()
        active = [g for g in report if g["status"] != "completed"]

        neglected = []
        memories = self.db.recall_memories()
        cutoff = datetime.now() - timedelta(days=days)

        for goal in active:
            keywords = [w.lower() for w in goal["description"].split() if len(w) > 3]
            has_recent = False
            for m_content, m_time, m_cat in memories:
                try:
                    m_dt = datetime.strptime(m_time.split('.')[0], "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    continue
                if m_dt > cutoff and any(kw in m_content.lower() for kw in keywords):
                    has_recent = True
                    break
            if not has_recent:
                neglected.append(goal)
        return neglected

    def update_progress(self, goal_id, progress, next_action=None):
        """Update a goal's progress percentage and next action."""
        self.db.update_goal_progress(goal_id, progress, next_action)

    def get_daily_recommendation(self):
        """Analyze goals + recent activity and suggest what to do today."""
        neglected = self.get_neglected_goals(days=2)
        top_goal = self.get_top_priority_goal()

        recommendations = []

        # Prioritize neglected high-priority goals
        for g in neglected:
            if g["priority"] == "high":
                action = g.get("next_action") or f"Work on '{g['description']}'"
                recommendations.append({
                    "goal": g["description"],
                    "priority": "high",
                    "reason": "neglected",
                    "suggestion": action
                })

        # Then the top priority goal if not already suggested
        if top_goal and not any(r["goal"] == top_goal["description"] for r in recommendations):
            action = top_goal.get("next_action") or f"Continue '{top_goal['description']}'"
            recommendations.append({
                "goal": top_goal["description"],
                "priority": top_goal["priority"],
                "reason": "top_priority",
                "suggestion": action
            })

        # Add remaining neglected goals
        for g in neglected:
            if not any(r["goal"] == g["description"] for r in recommendations):
                action = g.get("next_action") or f"Spend time on '{g['description']}'"
                recommendations.append({
                    "goal": g["description"],
                    "priority": g["priority"],
                    "reason": "neglected",
                    "suggestion": action
                })

        return recommendations
