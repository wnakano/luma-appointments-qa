from ...states.conversational_qa import QAState
from ...types.conversational_qa import (
    Routes, 
    IntentType
)
from utils import Logger

logger = Logger(__name__)


class CancelAppointmentNode:
    def __init__(
        self,
    ) -> None:
        pass
    
    def __call__(self, state: QAState) -> QAState:
        logger.info("[NODE] CancelAppointmentNode")
        return state

