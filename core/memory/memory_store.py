import os
import sys
from datetime import datetime, timedelta
from core.memory import DatabaseManager

class MemoryStore:
    def __init__(self, db_manager=None):
        if db_manager is None:
            self.db = DatabaseManager()
        else:
            self.db = db_manager
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
