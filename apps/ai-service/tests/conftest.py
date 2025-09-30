"""
Pytest configuration and fixtures for ai-service tests.

This is the root conftest.py file that provides global fixtures and configuration
for all tests in the ai-service project.
"""
import os
import sys
from pathlib import Path
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool


project_root = Path(__file__).parent.parent
ai_service_src_path = project_root / "src"
apps_path = project_root.parent

print(f"ai_service_src_path = {ai_service_src_path}")
print(f"apps_path = {apps_path}")

# Insert paths if not already present
if str(ai_service_src_path) not in sys.path:
    sys.path.insert(0, str(ai_service_src_path))
if str(apps_path) not in sys.path:
    sys.path.insert(0, str(apps_path))


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )


@pytest.fixture(scope="session")
def test_env_vars():
    """Set up test environment variables."""
    os.environ["DATABASE_URL"] = "postgresql://test:test@localhost:5432/test_db"
    os.environ["OPENAI_API_KEY"] = "test-key-12345"
    os.environ["MCP_SERVER_URL"] = "http://localhost:8001"
    return os.environ


@pytest.fixture
def test_client():
    """Create a FastAPI test client."""
    from app import create_app
    app = create_app()
    return TestClient(app)


@pytest.fixture
def mock_database_engine():
    """Mock database engine for testing."""
    with patch("infrastructure.database.orm.engine.DatabaseEngine") as mock:
        mock_instance = Mock()
        mock_session = Mock()
        mock_instance.get_session.return_value = mock_session
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_database_session():
    """Mock database session."""
    session = Mock(spec=Session)
    session.query = Mock()
    session.commit = Mock()
    session.rollback = Mock()
    session.close = Mock()
    return session


@pytest.fixture
def in_memory_db_engine():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    yield engine, TestingSessionLocal
    
    engine.dispose()


@pytest.fixture
async def mock_mcp_client():
    """Mock MCP client for testing."""
    mock_client = AsyncMock()
    mock_client.list_tools = AsyncMock(return_value=[
        {
            "name": "db_query",
            "description": "Execute a database query",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "params": {"type": "array"}
                }
            }
        }
    ])
    mock_client.call_tool = AsyncMock(return_value={"status": "success"})
    return mock_client


@pytest.fixture
def mock_llm_response():
    """Factory for creating mock LLM responses."""
    def _create_response(content: str, **kwargs):
        mock = Mock()
        mock.content = content
        for key, value in kwargs.items():
            setattr(mock, key, value)
        return mock
    return _create_response


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client."""
    with patch("langchain_openai.ChatOpenAI") as mock:
        mock_instance = Mock()
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def sample_user_info():
    """Sample user information for testing.
    
    Note: This is the canonical user info fixture. Use this for general tests.
    Service-specific tests may have their own specialized fixtures.
    """
    return {
        "name": "John Doe",
        "phone": "555-1234",
        "dob": "1990-01-01",
        "email": "john.doe@example.com"
    }


@pytest.fixture
def sample_appointments():
    """Sample appointments data for testing."""
    return {
        "1": {
            "id": "1",
            "date": "2025-10-01",
            "time": "10:00 AM",
            "doctor": "Dr. Smith",
            "type": "Consultation",
            "status": "scheduled"
        },
        "2": {
            "id": "2",
            "date": "2025-10-05",
            "time": "2:00 PM",
            "doctor": "Dr. Jones",
            "type": "Follow-up",
            "status": "scheduled"
        }
    }


@pytest.fixture
def sample_qa_payload():
    """Sample QA payload for testing chatbot requests."""
    return {
        "request_id": "test-request-123",
        "user_id": "test-user-456",
        "user_message": "I want to schedule an appointment",
        "session_id": "test-session-789"
    }


@pytest.fixture
def sample_qa_state():
    """Sample QA state for testing graph nodes."""
    return {
        "user_message": "My name is John Doe",
        "session_id": "test-session-789",
        "history": [],
        "messages": [],
        "verification_step": "name",
        "user_verified": False,
        "collected_info": {},
        "user_info": {},
        "user_info_db": {},
        "current_node": "check_user_session",
        "route": "collect",
        "assistant_message": None,
        "menu_options": None,
        "appointments": None,
        "selected_appointment": None,
        "selected_action": None,
        "selected_menu_choice": None,
        "phase": None,
        "menu": None,
        "error_message": None,
        "retry_count": 0
    }
