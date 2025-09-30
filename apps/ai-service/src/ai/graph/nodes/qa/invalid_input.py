from typing import Any, Dict, Optional


from ...states.qa import QAState
from ...types.qa import IdentificationState, Nodes

from utils import Logger

logger = Logger(__name__)


class HandleInvalidInputNode:
    def __init__(self):
        pass
    
    def __call__(
        self, 
        state: QAState
    ) -> QAState:
        logger.info("[NODE] Handling invalid input")
        state["current_node"] = Nodes.HANDLE_INVALID_INPUT
        logger.info(f"Handling invalid input for step={state.get('verification_step')}")
        err = state.get("error_message")
        
        if err:
            return {
                **state,
                "messages": state.get("messages", []) + [err],
            }

        return state

