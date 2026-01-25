"""
LUMA Simple Memory - Notes only, no reminders.
"""

import sqlite3
from pathlib import Path
from typing import List, Optional
import re


class Memory:
    """Simple memory for notes."""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = str(Path.home() / ".luma" / "memory.db")
        
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
    
    def add(self, content: str) -> str:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT INTO notes (content) VALUES (?)", (content,))
            conn.commit()
        return "Got it, I'll remember that!"
    
    def search(self, query: str) -> List[dict]:
        keywords = self._extract_keywords(query)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM notes WHERE content LIKE ? ORDER BY created_at DESC LIMIT 10",
                (f"%{keywords}%",)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def get_recent(self, limit: int = 5) -> List[dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM notes ORDER BY created_at DESC LIMIT ?",
                (limit,)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def delete_by_topic(self, topic: str) -> str:
        keywords = self._extract_keywords(topic)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT id, content FROM notes WHERE content LIKE ?",
                (f"%{keywords}%",)
            )
            matches = cursor.fetchall()
            
            if not matches:
                return f"No notes found about '{topic}'."
            
            ids = [m[0] for m in matches]
            placeholders = ",".join(["?" for _ in ids])
            conn.execute(f"DELETE FROM notes WHERE id IN ({placeholders})", ids)
            conn.commit()
            
            return f"Deleted {len(matches)} note(s)."
    
    def clear_all(self) -> str:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM notes")
            conn.commit()
        return "All notes cleared!"
    
    def count(self) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM notes")
            return cursor.fetchone()[0]
    
    def format_notes(self) -> str:
        notes = self.get_recent(10)
        if not notes:
            return "No notes saved."
        
        result = [f"You have {len(notes)} note(s):"]
        for n in notes:
            result.append(f"  • {n['content']}")
        return " ".join(result)
    
    def _extract_keywords(self, text: str) -> str:
        stop_words = {'the', 'a', 'an', 'is', 'are', 'to', 'of', 'in', 'for', 
                     'on', 'with', 'at', 'by', 'from', 'that', 'this', 'my',
                     'about', 'note', 'okay', 'ok', 'please'}
        words = re.findall(r'\b[a-zA-Z0-9]{2,}\b', text.lower())
        keywords = [w for w in words if w not in stop_words]
        return ' '.join(keywords[:3])  # Take first 3 keywords


_memory: Optional[Memory] = None


def get_memory() -> Memory:
    global _memory
    if _memory is None:
        _memory = Memory()
    return _memory
