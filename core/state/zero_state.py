from datetime import datetime


class ZeroState:
    """Tracks Zero's runtime state for the current session."""

    def __init__(self):
        self.current_user = "Varun"
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_start = datetime.now()
        self.commands_this_session = 0
        self.last_command = None
        self.last_command_time = None
        self.last_action_type = None
        self.active_goal = None
        self.current_task = None
        self.errors_this_session = 0

    def record_command(self, command_text, action_type=None):
        """Update state after a command is processed."""
        self.commands_this_session += 1
        self.last_command = command_text
        self.last_command_time = datetime.now()
        if action_type:
            self.last_action_type = action_type

    def record_error(self):
        """Track an error occurrence."""
        self.errors_this_session += 1

    def set_active_goal(self, goal_description):
        """Set the currently active goal."""
        self.active_goal = goal_description

    def set_current_task(self, task_description):
        """Set what Zero is currently working on."""
        self.current_task = task_description

    def get_session_duration_minutes(self):
        """How long this session has been running."""
        delta = datetime.now() - self.session_start
        return round(delta.total_seconds() / 60, 1)

    def get_snapshot(self):
        """Returns a serializable snapshot of current state for context saving."""
        return {
            "current_user": self.current_user,
            "session_id": self.session_id,
            "session_start": self.session_start.strftime("%Y-%m-%d %H:%M:%S"),
            "commands_processed": self.commands_this_session,
            "last_command": self.last_command,
            "last_action_type": self.last_action_type,
            "active_goal": self.active_goal,
            "current_task": self.current_task,
            "session_duration_minutes": self.get_session_duration_minutes(),
            "errors": self.errors_this_session
        }

    def get_session_summary(self):
        """Human-readable session summary for reflection."""
        duration = self.get_session_duration_minutes()
        lines = [f"Session: {self.session_id}"]
        lines.append(f"Duration: {duration} minutes")
        lines.append(f"Commands processed: {self.commands_this_session}")
        if self.last_command:
            lines.append(f"Last command: {self.last_command}")
        if self.active_goal:
            lines.append(f"Active goal: {self.active_goal}")
        if self.current_task:
            lines.append(f"Current task: {self.current_task}")
        if self.errors_this_session > 0:
            lines.append(f"Errors encountered: {self.errors_this_session}")
        return "\n".join(lines)
