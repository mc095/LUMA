"""Tests for the database repository."""

import pytest
from datetime import datetime

from luma.db.repository import Repository
from luma.db.models import Session, Message


class TestSessionOperations:
    """Tests for session CRUD operations."""
    
    def test_create_session(self, test_repository):
        """Test creating a new session."""
        session = test_repository.create_session(title="Test Session")
        
        assert session is not None
        assert session.id is not None
        assert session.title == "Test Session"
        assert session.is_active == True
    
    def test_create_session_default_title(self, test_repository):
        """Test creating session with default title."""
        session = test_repository.create_session()
        
        assert session.title == "New Conversation"
    
    def test_get_session(self, test_repository, test_session):
        """Test retrieving a session by ID."""
        retrieved = test_repository.get_session(test_session.id)
        
        assert retrieved is not None
        assert retrieved.id == test_session.id
    
    def test_get_nonexistent_session(self, test_repository):
        """Test retrieving a session that doesn't exist."""
        result = test_repository.get_session("nonexistent-id")
        
        assert result is None
    
    def test_get_all_sessions(self, test_repository):
        """Test listing all sessions."""
        # Create multiple sessions
        test_repository.create_session(title="Session 1")
        test_repository.create_session(title="Session 2")
        test_repository.create_session(title="Session 3")
        
        sessions = test_repository.get_all_sessions()
        
        assert len(sessions) >= 3
    
    def test_delete_session(self, test_repository, test_session):
        """Test soft-deleting a session."""
        result = test_repository.delete_session(test_session.id)
        
        assert result == True
        
        # Session should no longer appear in active list
        sessions = test_repository.get_all_sessions()
        ids = [s.id for s in sessions]
        assert test_session.id not in ids


class TestMessageOperations:
    """Tests for message operations."""
    
    def test_add_message(self, test_repository, test_session):
        """Test adding a message to a session."""
        message = test_repository.add_message(
            session_id=test_session.id,
            role="user",
            content="Hello!"
        )
        
        assert message is not None
        assert message.role == "user"
        assert message.content == "Hello!"
    
    def test_add_message_with_metadata(self, test_repository, test_session):
        """Test adding a message with metadata."""
        message = test_repository.add_message(
            session_id=test_session.id,
            role="assistant",
            content="Here are the search results",
            metadata={"tools_used": ["duckduckgo_search"]}
        )
        
        # Note: metadata is stored in extra_data field
        assert message is not None
        assert message.content == "Here are the search results"
    
    def test_get_messages(self, test_repository, test_session):
        """Test retrieving messages for a session."""
        # Add some messages
        test_repository.add_message(test_session.id, "user", "Message 1")
        test_repository.add_message(test_session.id, "assistant", "Response 1")
        test_repository.add_message(test_session.id, "user", "Message 2")
        
        messages = test_repository.get_messages(test_session.id)
        
        assert len(messages) == 3
    
    def test_get_recent_messages(self, test_repository, test_session):
        """Test retrieving recent messages."""
        # Add several messages
        for i in range(10):
            test_repository.add_message(test_session.id, "user", f"Message {i}")
        
        recent = test_repository.get_recent_messages(test_session.id, limit=5)
        
        assert len(recent) == 5
        # Should be in chronological order (oldest first)
        assert "Message 5" in recent[0].content
    
    def test_clear_session_messages(self, test_repository, test_session):
        """Test clearing all messages in a session."""
        # Add messages
        test_repository.add_message(test_session.id, "user", "Test 1")
        test_repository.add_message(test_session.id, "user", "Test 2")
        
        # Clear
        count = test_repository.clear_session_messages(test_session.id)
        
        assert count == 2
        
        # Verify empty
        messages = test_repository.get_messages(test_session.id)
        assert len(messages) == 0
