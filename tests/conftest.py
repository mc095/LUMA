"""Pytest configuration and fixtures."""

import pytest
import asyncio
from typing import Generator

from luma.db.models import Base
from luma.db.repository import Repository
from luma.config import settings


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def test_repository():
    """Create a test repository with in-memory database."""
    repo = Repository(database_url="sqlite:///:memory:")
    yield repo


@pytest.fixture
def test_session(test_repository):
    """Create a test session."""
    session = test_repository.create_session(title="Test Session")
    return session
