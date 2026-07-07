import os
import sys
import json
from datetime import datetime, timedelta
from core.memory import DatabaseManager

class MemoryStore:
    def __init__(self, db_manager=None):
        if db_manager is None:
            self.db = DatabaseManager()
        else:
            self.db = db_manager
        self._short_term = []  # In-memory conversation buffer
        self._session_id = None
        self._init_extended_tables()

    def _init_extended_tables(self):
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            
            # Habits Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS habits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                last_logged TEXT,
                streak INTEGER DEFAULT 0
            );
            """)

            # Projects Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                status TEXT DEFAULT 'active'
            );
            """)
            conn.commit()

    # --- Preferences & Context ---
    def save_preference(self, key, value):
        content = f"{key}: {value}"
        # Avoid duplicates by searching for existing memory first
        existing = self.db.recall_memories(key)
        for m in existing:
            if m[0].startswith(f"{key}:"):
                with self.db._get_connection() as conn:
                    conn.cursor().execute("DELETE FROM memories WHERE content = ?", (m[0],))
                    conn.commit()
        return self.db.save_memory(content, category="preferences")

    def get_preferences(self):
        memories = self.db.recall_memories()
        prefs = {}
        for m in memories:
            content, timestamp, category = m
            if category == "preferences" or (content and ":" in content and any(k in content.lower() for k in ["prefer", "like", "habit", "schedule"])):
                parts = content.split(":", 1)
                if len(parts) == 2:
                    prefs[parts[0].strip().lower()] = parts[1].strip()
        return prefs

    # --- Habits ---
    def add_habit(self, name):
        try:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO habits (name) VALUES (?)", (name,))
                conn.commit()
                return cursor.lastrowid
        except Exception:
            # Already exists
            return None

    def log_habit_activity(self, name):
        self.add_habit(name)  # Ensure it exists
        
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT last_logged, streak FROM habits WHERE name = ?", (name,))
            row = cursor.fetchone()
            if not row:
                return False
                
            last_logged, streak = row
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if not last_logged:
                new_streak = 1
            else:
                try:
                    last_dt = datetime.strptime(last_logged, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    last_dt = datetime.now()
                
                delta = datetime.now().date() - last_dt.date()
                if delta.days == 1:
                    new_streak = streak + 1
                elif delta.days > 1:
                    new_streak = 1
                else:
                    new_streak = streak  # Same day log, keep streak
            
            cursor.execute(
                "UPDATE habits SET last_logged = ?, streak = ? WHERE name = ?",
                (now_str, new_streak, name)
            )
            conn.commit()
            return new_streak

    def get_habits(self):
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name, last_logged, streak FROM habits")
            return cursor.fetchall()

    # --- Projects ---
    def add_project(self, name, description=""):
        try:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO projects (name, description) VALUES (?, ?)", (name, description))
                conn.commit()
                return cursor.lastrowid
        except Exception:
            return None

    def get_projects(self):
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name, description, status FROM projects")
            return cursor.fetchall()

    def get_recent_context(self, limit=5):
        memories = self.db.recall_memories()
        conversations = self.db.get_conversations("default_session")
        
        recent_mems = memories[:limit]
        recent_convs = conversations[-limit:] if conversations else []
        
        return {
            "memories": [m[0] for m in recent_mems],
            "conversations": [{"role": c[0], "content": c[1]} for c in recent_convs]
        }

    # === SHORT-TERM MEMORY (in-memory, current session only) ===
    def push_turn(self, role, content):
        """Add a turn to the current conversation buffer."""
        self._short_term.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        # Keep only last 50 turns in memory
        if len(self._short_term) > 50:
            self._short_term = self._short_term[-50:]

    def get_conversation_context(self, n=10):
        """Get the last N turns from short-term memory."""
        return self._short_term[-n:]

    def clear_short_term(self):
        """Clear the conversation buffer."""
        self._short_term = []

    # === LONG-TERM MEMORY (persistent in SQLite) ===
    def save_fact(self, key, value, category="general"):
        """Save a permanent fact. Updates existing key if found."""
        existing = self.db.recall_memories(key)
        for m in existing:
            if m[0].startswith(f"{key}:"):
                with self.db._get_connection() as conn:
                    conn.cursor().execute("DELETE FROM memories WHERE content = ?", (m[0],))
                    conn.commit()
        content = f"{key}: {value}"
        return self.db.save_memory(content, category=category)

    def recall_facts(self, query=None, category=None):
        """Search long-term memory, optionally filtered by category."""
        all_memories = self.db.recall_memories(query)
        if category:
            return [m for m in all_memories if m[2] == category]
        return all_memories

    def get_user_profile(self):
        """Build a dict of known facts about the user."""
        prefs = self.get_preferences()
        projects = self.get_projects()
        habits = self.get_habits()
        return {
            "name": "Varun",
            "preferences": prefs,
            "projects": [(p[0], p[1], p[2]) for p in projects],
            "habits": [(h[0], h[1], h[2]) for h in habits]
        }

    # === CONTEXT MEMORY (session continuity) ===
    def start_session(self, session_id):
        """Begin a new session."""
        self._session_id = session_id
        self._short_term = []
        self.db.start_session(session_id)

    def save_session_context(self, context_dict):
        """Save a snapshot of what was happening when session ends."""
        if self._session_id:
            summary_parts = []
            if context_dict.get("commands_processed"):
                summary_parts.append(f"Processed {context_dict['commands_processed']} commands")
            if context_dict.get("last_command"):
                summary_parts.append(f"Last command: {context_dict['last_command']}")
            summary = ". ".join(summary_parts) if summary_parts else "Session ended."

            self.db.end_session(self._session_id, summary)
            self.db.save_context_snapshot(self._session_id, context_dict)

    def load_last_session_context(self):
        """Load the snapshot from the most recent previous session."""
        return self.db.get_last_context_snapshot()

    def get_continuity_summary(self):
        """Generate a human-readable summary of what happened last session."""
        last_session = self.db.get_last_session()
        last_context = self.load_last_session_context()

        if not last_session:
            return None

        session_id, start_time, end_time, summary = last_session

        result = {"session_id": session_id, "start_time": start_time}
        if end_time:
            result["end_time"] = end_time
        if summary:
            result["summary"] = summary
        if last_context:
            result["context"] = last_context
        return result
