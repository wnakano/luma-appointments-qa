"""Tests for ValidationService."""
import pytest
from unittest.mock import Mock, patch

from ..conftest import DEFAULT_MODEL, DEFAULT_TEMPERATURE


@pytest.mark.unit
@pytest.mark.asyncio
class TestValidationService:
    """Test cases for ValidationService."""
    
    async def test_validation_service_initialization(self, mock_openai_llm):
        """Test that ValidationService initializes successfully with default parameters."""
        from ai.graph.services.qa.validation import ValidationService
        
        service = ValidationService(model=DEFAULT_MODEL, temp=DEFAULT_TEMPERATURE)
        
        assert service is not None
        assert hasattr(service, 'llm')
        assert hasattr(service, 'prompt_builder')
    
    async def test_validate_valid_phone(self):
        """Test validating a correctly formatted phone number."""
        from ai.graph.services.qa.validation import ValidationService
        from ai.graph.models.qa import ValidationResult
        
        mock_validation = ValidationResult(
            is_valid=True,
            cleaned_value="555-1234",
            error_message=None,
            suggestions=None
        )
        mock_chain = Mock()
        mock_chain.invoke = Mock(return_value=mock_validation)
        
        with patch("ai.graph.services.llm.ChatOpenAI"):
            service = ValidationService(model=DEFAULT_MODEL, temp=DEFAULT_TEMPERATURE)
            
            with patch.object(service, 'build_structured_chain', return_value=mock_chain):
                result = service.run(
                    value="555-1234",
                    info_type="phone"
                )
                
                assert result is not None
                assert isinstance(result, ValidationResult)
                assert result.is_valid is True
                mock_chain.invoke.assert_called_once()
    
    async def test_validate_invalid_phone(self):
        """Test validating an incorrectly formatted phone number."""
        from ai.graph.services.qa.validation import ValidationService
        from ai.graph.models.qa import ValidationResult
        
        mock_validation = ValidationResult(
            is_valid=False,
            cleaned_value=None,
            error_message="Invalid phone number format",
            suggestions=["Try format: XXX-XXXX"]
        )
        mock_chain = Mock()
        mock_chain.invoke = Mock(return_value=mock_validation)
        
        with patch("ai.graph.services.llm.ChatOpenAI"):
            service = ValidationService(model=DEFAULT_MODEL, temp=DEFAULT_TEMPERATURE)
            
            with patch.object(service, 'build_structured_chain', return_value=mock_chain):
                result = service.run(
                    value="invalid",
                    info_type="phone"
                )
                
                assert result is not None
                assert isinstance(result, ValidationResult)
                assert result.is_valid is False
                assert result.error_message is not None
                mock_chain.invoke.assert_called_once()
    
    async def test_validate_date_of_birth(self):
        """Test validating a date of birth in ISO format."""
        from ai.graph.services.qa.validation import ValidationService
        from ai.graph.models.qa import ValidationResult
        
        mock_validation = ValidationResult(
            is_valid=True,
            cleaned_value="1990-01-01",
            error_message=None,
            suggestions=None
        )
        mock_chain = Mock()
        mock_chain.invoke = Mock(return_value=mock_validation)
        
        with patch("ai.graph.services.llm.ChatOpenAI"):
            service = ValidationService(model=DEFAULT_MODEL, temp=DEFAULT_TEMPERATURE)
            
            with patch.object(service, 'build_structured_chain', return_value=mock_chain):
                result = service.run(
                    value="1990-01-01",
                    info_type="dob"
                )
                
                assert result is not None
                assert isinstance(result, ValidationResult)
                assert result.is_valid is True
                assert result.cleaned_value == "1990-01-01"
                mock_chain.invoke.assert_called_once()
