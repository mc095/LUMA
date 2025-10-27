"""SQLite database management for LUMA."""

import sqlite3
from datetime import datetime
import atexit

class MessageDatabase:
    """Manages chat history in SQLite database."""
    
    def __init__(self, db_path="chat_history.db"):
        """Initialize database connection and create tables if needed."""
        self.db_path = db_path
        self.conn = None
        self._connect()
        atexit.register(self.close)
    
    def _connect(self):
        """Create database connection."""
        if not self.conn:
            self.conn = sqlite3.connect(self.db_path)
            self._init_db()
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def _init_db(self):
        """Create the messages table if it doesn't exist."""
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()
    
    def add_message(self, role: str, content: str):
        """Add a new message to the database."""
        self._connect()
        self.conn.execute(
            'INSERT INTO messages (role, content, timestamp) VALUES (?, ?, ?)',
            (role, content, datetime.now().isoformat())
        )
        self.conn.commit()
    
    def get_recent_messages(self, limit: int = 10) -> list:
        """Get the most recent messages from the database."""
        self._connect()
        cursor = self.conn.execute(
            'SELECT role, content FROM messages ORDER BY timestamp DESC LIMIT ?',
            (limit,)
        )
        return [{'role': role, 'content': content} for role, content in cursor.fetchall()]
    
    def clear_history(self):
        """Clear all message history."""
        self._connect()
        self.conn.execute('DELETE FROM messages')
        self.conn.commit()