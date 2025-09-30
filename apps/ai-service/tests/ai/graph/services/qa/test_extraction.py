"""Tests for ExtractionService."""
import pytest
from unittest.mock import Mock, patch

from ..conftest import DEFAULT_MODEL, DEFAULT_TEMPERATURE


@pytest.mark.unit
@pytest.mark.asyncio
class TestExtractionService:
    """Test cases for ExtractionService."""
    
    async def test_extraction_service_initialization(self, mock_openai_llm):
        """Test that ExtractionService initializes successfully with default parameters."""
        from ai.graph.services.qa.extraction import ExtractionService
        
        service = ExtractionService(model=DEFAULT_MODEL, temp=DEFAULT_TEMPERATURE)
        
        assert service is not None
        assert hasattr(service, 'llm')
        assert hasattr(service, 'prompt_builder')
    
    async def test_extract_user_info(self):
        """Test extracting complete user information from a message."""
        from ai.graph.services.qa.extraction import ExtractionService
        from ai.graph.models.qa import ExtractedUserInfo
        
        # Mock extracted info
        mock_extracted = ExtractedUserInfo(
            full_name="John Doe",
            phone_number="555-1234",
            birthday=None
        )
        mock_chain = Mock()
        mock_chain.invoke = Mock(return_value=mock_extracted)
        
        with patch("ai.graph.services.llm.ChatOpenAI"):
            service = ExtractionService(model=DEFAULT_MODEL, temp=DEFAULT_TEMPERATURE)
            
            with patch.object(service, 'build_structured_chain', return_value=mock_chain):
                result = service.run(
                    user_message="My name is John Doe and my phone is 555-1234",
                    info_type="name",
                    collected_info={}
                )
                
                assert result is not None
                assert isinstance(result, ExtractedUserInfo)
                mock_chain.invoke.assert_called_once()
    
    async def test_extract_partial_info(self):
        """Test extracting partial user information (name only)."""
        from ai.graph.services.qa.extraction import ExtractionService
        from ai.graph.models.qa import ExtractedUserInfo
        
        # Mock partial extracted info
        mock_extracted = ExtractedUserInfo(
            full_name="Jane Smith",
            phone_number=None,
            birthday=None
        )
        mock_chain = Mock()
        mock_chain.invoke = Mock(return_value=mock_extracted)
        
        with patch("ai.graph.services.llm.ChatOpenAI"):
            service = ExtractionService(model=DEFAULT_MODEL, temp=DEFAULT_TEMPERATURE)
            
            with patch.object(service, 'build_structured_chain', return_value=mock_chain):
                result = service.run(
                    user_message="I'm Jane Smith",
                    info_type="name",
                    collected_info={}
                )
                
                assert result is not None
                assert isinstance(result, ExtractedUserInfo)
                assert result.full_name == "Jane Smith"
                mock_chain.invoke.assert_called_once()
