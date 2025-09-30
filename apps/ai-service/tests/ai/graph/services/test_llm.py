"""Tests for base LLMService class."""
import pytest
from unittest.mock import patch

from .conftest import DEFAULT_MODEL, DEFAULT_TEMPERATURE


@pytest.mark.unit
class TestLLMService:
    """Test cases for base LLMService class."""
    
    @patch("ai.graph.services.llm.ChatOpenAI")
    def test_llm_service_initialization(self, mock_openai):
        """Test that base LLMService initializes with LLM and prompt builder."""
        from ai.graph.services.llm import LLMService
        
        service = LLMService(model=DEFAULT_MODEL, temp=DEFAULT_TEMPERATURE)
        
        assert service is not None
        assert service.llm is not None
        assert service.prompt_builder is not None
        mock_openai.assert_called_once()
