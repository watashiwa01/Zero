class GoalsManager:
    def __init__(self, db_manager):
        self.db = db_manager

    def create_goal_with_tasks(self, description, tasks_list=None, target_date=None):
        goal_id = self.db.add_goal(description, target_date)
        created_tasks = []
        if tasks_list:
            for task_title in tasks_list:
                task_id = self.db.add_task(task_title, goal_id=goal_id)
                created_tasks.append((task_id, task_title))
        return goal_id, created_tasks

    def get_goal_status_report(self):
        goals = self.db.get_goals()
        tasks = self.db.get_tasks()
        
        report = []
        for g in goals:
            g_id, g_desc, g_date, g_status = g
            g_tasks = [t for t in tasks if t[4] == g_id] # Match goal_id
            completed = sum(1 for t in g_tasks if t[2] == 'completed')
            total = len(g_tasks)
            
            report.append({
                "id": g_id,
                "description": g_desc,
                "target_date": g_date,
                "status": g_status,
                "progress": f"{completed}/{total}" if total > 0 else "No tasks"
            })
        return report
