"""Tests for IntentService."""
import pytest
from unittest.mock import Mock, patch

from ..conftest import DEFAULT_MODEL, DEFAULT_TEMPERATURE


@pytest.mark.unit
class TestIntentService:
    """Test cases for IntentService."""
    
    def test_intent_service_initialization(self, mock_openai_llm):
        """Test that IntentService initializes successfully with default parameters."""
        from ai.graph.services.qa.intent import IntentService
        
        service = IntentService(model=DEFAULT_MODEL, temp=DEFAULT_TEMPERATURE)
        
        assert service is not None
        assert hasattr(service, 'llm')
        assert hasattr(service, 'prompt_builder')
    
    def test_classify_appointment_intent(
        self,
        sample_user_message,
        sample_verification_step,
        sample_history
    ):
        """Test that IntentService correctly classifies appointment scheduling intent."""
        from ai.graph.services.qa.intent import IntentService
        from ai.graph.models.qa import UserIntent

        mock_intent = UserIntent(
            is_providing_info=True,
            is_asking_question=False,
            is_correction=False,
            wants_to_skip=False
        )
        
        mock_chain = Mock()
        mock_chain.invoke = Mock(return_value=mock_intent)
        
        with patch("ai.graph.services.llm.ChatOpenAI"):
            service = IntentService(model=DEFAULT_MODEL, temp=DEFAULT_TEMPERATURE)
            
            with patch.object(service, 'build_structured_chain', return_value=mock_chain):
                result = service.run(
                    user_message=sample_user_message,
                    verification_step=sample_verification_step,
                    history=sample_history
                )
                
                assert isinstance(result, UserIntent)
                assert result.is_providing_info is True
                mock_chain.invoke.assert_called_once()
    
    def test_classify_cancellation_intent(
        self,
        mock_openai_llm,
        sample_verification_step,
        sample_history
    ):
        """Test that IntentService correctly classifies cancellation intent."""
        from ai.graph.services.qa.intent import IntentService
        from ai.graph.models.qa import UserIntent
        
        mock_chain = Mock()
        mock_chain.invoke = Mock(return_value=UserIntent(**{    
            "is_providing_info": False,
            "is_asking_question": False,
            "is_correction": False,
            "wants_to_skip": False,
        }))

        service = IntentService(model=DEFAULT_MODEL, temp=DEFAULT_TEMPERATURE)
        
        with patch.object(IntentService, 'build_structured_chain', return_value=mock_chain):
            result = service.run(
                user_message="I need to cancel my appointment",
                verification_step=sample_verification_step,
                history=sample_history
            )
            
            assert isinstance(result, UserIntent)
