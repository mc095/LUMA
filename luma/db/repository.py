"""Database repository for session and message management."""

from typing import Optional, List
from datetime import datetime
from dataclasses import dataclass

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .models import Base, Session, Message
from ..config import settings


@dataclass
class SessionData:
    """Detached session data."""
    id: str
    title: str
    summary: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_active: bool = True


@dataclass
class MessageData:
    """Detached message data."""
    id: str
    session_id: str
    role: str
    content: str
    created_at: Optional[datetime] = None


class Repository:
    """Database repository for LUMA."""
    
    def __init__(self, database_url: str = None):
        """
        Initialize repository.
        
        Args:
            database_url: SQLAlchemy database URL (default: from settings)
        """
        self.database_url = database_url or settings.database_url
        self.engine = create_engine(self.database_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine, expire_on_commit=False)
        
        # Create tables
        Base.metadata.create_all(self.engine)
    
    def _session_to_data(self, session: Session) -> SessionData:
        """Convert Session ORM object to dataclass."""
        return SessionData(
            id=session.id,
            title=session.title,
            summary=session.summary,
            created_at=session.created_at,
            updated_at=session.updated_at,
            is_active=session.is_active
        )
    
    def _message_to_data(self, message: Message) -> MessageData:
        """Convert Message ORM object to dataclass."""
        return MessageData(
            id=message.id,
            session_id=message.session_id,
            role=message.role,
            content=message.content,
            created_at=message.created_at
        )
    
    # Session operations
    
    def create_session(self, title: str = "New Conversation") -> SessionData:
        """Create a new conversation session."""
        db = self.SessionLocal()
        try:
            session = Session(title=title)
            db.add(session)
            db.commit()
            db.refresh(session)
            return self._session_to_data(session)
        finally:
            db.close()
    
    def get_session(self, session_id: str) -> Optional[SessionData]:
        """Get a session by ID."""
        db = self.SessionLocal()
        try:
            session = db.query(Session).filter(Session.id == session_id).first()
            return self._session_to_data(session) if session else None
        finally:
            db.close()
    
    def get_all_sessions(self, limit: int = 50) -> List[SessionData]:
        """Get all sessions, ordered by most recent."""
        db = self.SessionLocal()
        try:
            sessions = db.query(Session)\
                .filter(Session.is_active == True)\
                .order_by(Session.updated_at.desc())\
                .limit(limit)\
                .all()
            return [self._session_to_data(s) for s in sessions]
        finally:
            db.close()
    
    def update_session_title(self, session_id: str, title: str) -> Optional[SessionData]:
        """Update session title."""
        db = self.SessionLocal()
        try:
            session = db.query(Session).filter(Session.id == session_id).first()
            if session:
                session.title = title
                session.updated_at = datetime.utcnow()
                db.commit()
                return self._session_to_data(session)
            return None
        finally:
            db.close()
    
    def delete_session(self, session_id: str) -> bool:
        """Soft delete a session."""
        db = self.SessionLocal()
        try:
            session = db.query(Session).filter(Session.id == session_id).first()
            if session:
                session.is_active = False
                db.commit()
                return True
            return False
        finally:
            db.close()
    
    # Message operations
    
    def add_message(
        self, 
        session_id: str, 
        role: str, 
        content: str, 
        metadata: dict = None
    ) -> MessageData:
        """Add a message to a session."""
        db = self.SessionLocal()
        try:
            message = Message(
                session_id=session_id,
                role=role,
                content=content,
                extra_data=metadata
            )
            db.add(message)
            
            # Update session timestamp
            session = db.query(Session).filter(Session.id == session_id).first()
            if session:
                session.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(message)
            return self._message_to_data(message)
        finally:
            db.close()
    
    def get_messages(
        self, 
        session_id: str, 
        limit: int = 100
    ) -> List[MessageData]:
        """Get messages for a session."""
        db = self.SessionLocal()
        try:
            messages = db.query(Message)\
                .filter(Message.session_id == session_id)\
                .order_by(Message.created_at.asc())\
                .limit(limit)\
                .all()
            return [self._message_to_data(m) for m in messages]
        finally:
            db.close()
    
    def get_recent_messages(
        self, 
        session_id: str, 
        limit: int = 10
    ) -> List[MessageData]:
        """Get the most recent messages for context."""
        db = self.SessionLocal()
        try:
            messages = db.query(Message)\
                .filter(Message.session_id == session_id)\
                .order_by(Message.created_at.desc())\
                .limit(limit)\
                .all()
            return list(reversed([self._message_to_data(m) for m in messages]))
        finally:
            db.close()
    
    def clear_session_messages(self, session_id: str) -> int:
        """Clear all messages in a session."""
        db = self.SessionLocal()
        try:
            count = db.query(Message)\
                .filter(Message.session_id == session_id)\
                .delete()
            db.commit()
            return count
        finally:
            db.close()


# Global repository instance
repository = Repository()
