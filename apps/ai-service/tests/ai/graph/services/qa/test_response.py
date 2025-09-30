"""Tests for ResponseService."""
import pytest
from unittest.mock import Mock, patch

from ..conftest import DEFAULT_MODEL, DEFAULT_TEMPERATURE


@pytest.mark.unit
@pytest.mark.asyncio
class TestResponseService:
    """Test cases for ResponseService."""
    
    async def test_response_service_initialization(self, mock_openai_llm):
        """Test that ResponseService initializes successfully with default parameters."""
        from ai.graph.services.qa.response import ResponseService
        
        service = ResponseService(model=DEFAULT_MODEL, temp=DEFAULT_TEMPERATURE)
        
        assert service is not None
        assert hasattr(service, 'llm')
        assert hasattr(service, 'prompt_builder')
    
    async def test_generate_greeting_response(self):
        """Test generating a friendly greeting response to user."""
        from ai.graph.services.qa.response import ResponseService
        
        expected_greeting = "Hello! How can I help you today?"
        mock_response = Mock()
        mock_response.content = expected_greeting
        mock_chain = Mock()
        mock_chain.invoke = Mock(return_value=mock_response)
        
        with patch("ai.graph.services.llm.ChatOpenAI"):
            service = ResponseService(model=DEFAULT_MODEL, temp=DEFAULT_TEMPERATURE)
            
            with patch.object(service, 'build_chain', return_value=mock_chain):
                result = service.run(
                    context={"phase": "greeting", "user_message": "Hello"}
                )
                
                assert result is not None
                assert isinstance(result, str)
                assert "Hello" in result
                assert len(result) > 0
                mock_chain.invoke.assert_called_once()
    
    async def test_generate_verification_response(self):
        """Test generating a verification prompt for name collection."""
        from ai.graph.services.qa.response import ResponseService
        
        mock_response = Mock()
        mock_response.content = "Please provide your name to verify your identity."
        mock_chain = Mock()
        mock_chain.invoke = Mock(return_value=mock_response)
        
        with patch("ai.graph.services.llm.ChatOpenAI"):
            service = ResponseService(model=DEFAULT_MODEL, temp=DEFAULT_TEMPERATURE)
            
            with patch.object(service, 'build_chain', return_value=mock_chain):
                result = service.run(
                    context={"phase": "verification", "step": "name"}
                )
                
                assert result is not None
                assert isinstance(result, str)
                assert "name" in result.lower()
                mock_chain.invoke.assert_called_once()
