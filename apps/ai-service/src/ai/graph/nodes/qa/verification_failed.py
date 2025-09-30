
from typing import Any, Dict
from ...states.qa import QAState
from ...services.qa import ResponseService
from ...types.qa import Nodes
from utils import Logger

logger = Logger(__name__)


class VerificationFailedNode:
    """Node to handle when user verification fails completely"""
    
    def __init__(self, response_service: ResponseService):
        self.response_service = response_service
    
    def __call__(self, state: QAState) -> QAState:
        """Handle verification failure and restart the verification process"""
        logger.info("[NODE] Verification Failed: restarting verification process")
        
        logger.info(f"state={state}")
        response_message = self.response_service.generate_verification_failed_response(
            state=state
        )
        
        updated_state = QAState(**{
            **state,
            "assistant_message": response_message,
            "messages": state.get("messages") + [response_message],
            "user_verified": False,
            "verification_step": "name", 
            "collected_info": {},
            "current_node": Nodes.VERIFICATION_FAILED,
            "route": "collect",
            "verification_attempts": state.get("verification_attempts", 0) + 1
        })
        
        logger.info(f"Verification failed, restarting collection process. Attempt: {updated_state.get('verification_attempts')}")
        return updated_state