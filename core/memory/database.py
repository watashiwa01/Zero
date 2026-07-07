import sqlite3
import os
import json
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path=None):
        if db_path is None:
            # Default to D:\ZERO OS\data\zero.db
            db_dir = r"D:\ZERO OS\data"
            os.makedirs(db_dir, exist_ok=True)
            db_path = os.path.join(db_dir, "zero.db")
        
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Goals Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                target_date TEXT,
                status TEXT DEFAULT 'pending'
            );
            """)

            # Tasks Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                due_date TEXT,
                goal_id INTEGER,
                FOREIGN KEY(goal_id) REFERENCES goals(id)
            );
            """)

            # Memories Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                category TEXT
            );
            """)

            # Conversations Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # Sessions Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL UNIQUE,
                start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                end_time DATETIME,
                summary TEXT
            );
            """)

            # Context Snapshots Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS context_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                snapshot_data TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # Safely add new columns to goals table
            try:
                cursor.execute("ALTER TABLE goals ADD COLUMN priority TEXT DEFAULT 'medium'")
            except sqlite3.OperationalError:
                pass  # Column already exists
            try:
                cursor.execute("ALTER TABLE goals ADD COLUMN progress INTEGER DEFAULT 0")
            except sqlite3.OperationalError:
                pass  # Column already exists
            try:
                cursor.execute("ALTER TABLE goals ADD COLUMN next_action TEXT")
            except sqlite3.OperationalError:
                pass  # Column already exists

            conn.commit()

    # --- Memory Operations ---
    def save_memory(self, content, category=None):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO memories (content, category) VALUES (?, ?)",
                (content, category)
            )
            conn.commit()
            return cursor.lastrowid

    def recall_memories(self, query=None):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if query:
                cursor.execute(
                    "SELECT content, timestamp, category FROM memories WHERE content LIKE ? ORDER BY timestamp DESC",
                    (f"%{query}%",)
                )
            else:
                cursor.execute(
                    "SELECT content, timestamp, category FROM memories ORDER BY timestamp DESC"
                )
            return cursor.fetchall()

    # --- Goal Operations ---
    def add_goal(self, description, target_date=None):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO goals (description, target_date) VALUES (?, ?)",
                (description, target_date)
            )
            conn.commit()
            return cursor.lastrowid

    def get_goals(self, status=None):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if status:
                cursor.execute(
                    "SELECT id, description, target_date, status, priority, progress, next_action "
                    "FROM goals WHERE status = ?", (status,)
                )
            else:
                cursor.execute(
                    "SELECT id, description, target_date, status, priority, progress, next_action "
                    "FROM goals"
                )
            return cursor.fetchall()

    # --- Task Operations ---
    def add_task(self, title, due_date=None, goal_id=None):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO tasks (title, due_date, goal_id) VALUES (?, ?, ?)",
                (title, due_date, goal_id)
            )
            conn.commit()
            return cursor.lastrowid

    def get_tasks(self, status=None):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if status:
                cursor.execute("SELECT id, title, status, due_date, goal_id FROM tasks WHERE status = ?", (status,))
            else:
                cursor.execute("SELECT id, title, status, due_date, goal_id FROM tasks")
            return cursor.fetchall()

    # --- Conversation Operations ---
    def save_conversation(self, session_id, role, content):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO conversations (session_id, role, content) VALUES (?, ?, ?)",
                (session_id, role, content)
            )
            conn.commit()
            return cursor.lastrowid

    def get_conversations(self, session_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT role, content, timestamp FROM conversations WHERE session_id = ? ORDER BY timestamp ASC",
                (session_id,)
            )
            return cursor.fetchall()

    # --- Session Operations ---
    def start_session(self, session_id):
        """Record the start of a new session."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO sessions (session_id) VALUES (?)",
                (session_id,)
            )
            conn.commit()
            return cursor.lastrowid

    def end_session(self, session_id, summary=""):
        """Mark a session as ended and store its summary."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE sessions SET end_time = CURRENT_TIMESTAMP, summary = ? WHERE session_id = ?",
                (summary, session_id)
            )
            conn.commit()

    def get_last_session(self):
        """Return the most recent session as (session_id, start_time, end_time, summary)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT session_id, start_time, end_time, summary FROM sessions ORDER BY start_time DESC LIMIT 1"
            )
            return cursor.fetchone()

    # --- Context Snapshot Operations ---
    def save_context_snapshot(self, session_id, snapshot_dict):
        """Persist a context snapshot as JSON for a given session."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO context_snapshots (session_id, snapshot_data) VALUES (?, ?)",
                (session_id, json.dumps(snapshot_dict))
            )
            conn.commit()
            return cursor.lastrowid

    def get_last_context_snapshot(self):
        """Return the most recent context snapshot as a dict, or None."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT snapshot_data FROM context_snapshots ORDER BY created_at DESC LIMIT 1"
            )
            row = cursor.fetchone()
            if row:
                return json.loads(row[0])
            return None

    # --- Updated Goal Operations ---
    def update_goal_progress(self, goal_id, progress, next_action=None):
        """Update a goal's completion progress (0-100) and optional next action."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE goals SET progress = ?, next_action = ? WHERE id = ?",
                (progress, next_action, goal_id)
            )
            conn.commit()

    def update_goal_priority(self, goal_id, priority):
        """Set a goal's priority (low, medium, high, critical)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE goals SET priority = ? WHERE id = ?",
                (priority, goal_id)
            )
            conn.commit()
