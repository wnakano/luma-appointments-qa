"""
Shared test fixtures for AI graph services.

This conftest provides fixtures specific to testing ai/graph/services modules.
These fixtures are automatically available to all tests in this directory and subdirectories.

For general fixtures (database, MCP client, etc.), see the root conftest.py.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4

# LLM Configuration
DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_TEMPERATURE = 0.1
LOW_TEMPERATURE = 0.0

# Test Data
TEST_USER_NAME = "John Doe"
TEST_PHONE = "555-1234"
TEST_DOB = "1990-01-01"
TEST_SESSION_ID = "test-session-789"

@pytest.fixture
def mock_openai_llm():
    """Mock ChatOpenAI instance for testing LLM services.
    
    Use this fixture when you need to mock the LLM initialization.
    For tests that need structured output, use local chain mocking instead.
    """
    with patch("ai.graph.services.llm.ChatOpenAI") as mock:
        mock_instance = Mock()
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_structured_chain():
    """Factory for creating mock structured output chains.
    
    Returns a factory function that creates mock chains returning specific models.
    
    Example:
        def test_something(mock_structured_chain):
            chain = mock_structured_chain(UserIntent(is_providing_info=True, ...))
            # chain.invoke() will return the provided UserIntent instance
    """
    def _create_chain(return_value):
        mock_chain = Mock()
        mock_chain.invoke = Mock(return_value=return_value)
        return mock_chain
    return _create_chain


# =============================================================================
# CONVERSATION CONTEXT FIXTURES
# =============================================================================

@pytest.fixture
def sample_user_message():
    """Sample user message for testing intent classification and extraction."""
    return "I want to book an appointment"


@pytest.fixture
def sample_verification_step():
    """Sample verification step (name, phone, or dob)."""
    return "name"


@pytest.fixture
def sample_history():
    """Sample conversation history (empty for new conversations)."""
    return []


@pytest.fixture
def sample_session_id():
    """Sample session ID for testing."""
    return TEST_SESSION_ID


@pytest.fixture
def sample_extracted_info():
    """Sample extracted user information (simplified format for services).
    
    This is different from root conftest's sample_user_info.
    Use this for testing extraction and validation services.
    """
    return {
        "name": TEST_USER_NAME,
        "phone": TEST_PHONE,
        "dob": TEST_DOB
    }


@pytest.fixture
def sample_user_intent():
    """Sample user intent data for testing intent classification."""
    return {
        "is_providing_info": True,
        "is_asking_question": False,
        "is_correction": False,
        "wants_to_skip": False
    }


@pytest.fixture
def sample_appointment():
    """Sample appointment data with UUID for testing query services.
    
    Note: This has a UUID id, different from root conftest's string id.
    """
    return {
        "id": uuid4(),
        "date": "2025-10-01",
        "time": "10:00 AM",
        "doctor": "Dr. Smith",
        "type": "Consultation",
        "status": "scheduled"
    }


@pytest.fixture
def sample_appointment_list():
    """Sample list of appointments for testing query results."""
    return [
        {
            "id": uuid4(),
            "date": "2025-10-01",
            "time": "10:00 AM",
            "doctor": "Dr. Smith",
            "type": "Consultation",
            "status": "scheduled"
        },
        {
            "id": uuid4(),
            "date": "2025-10-05",
            "time": "2:00 PM",
            "doctor": "Dr. Jones",
            "type": "Follow-up",
            "status": "confirmed"
        }
    ]


@pytest.fixture
def sample_validation_cases():
    """Sample validation test cases for different field types."""
    return {
        "valid_phone": "555-1234",
        "invalid_phone": "invalid",
        "valid_dob": "1990-01-01",
        "invalid_dob": "not-a-date",
        "valid_name": "John Doe",
        "invalid_name": ""
    }
