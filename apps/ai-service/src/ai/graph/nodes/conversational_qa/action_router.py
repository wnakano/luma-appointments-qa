from ...states.conversational_qa import QAState, StateKeys
from ...types.conversational_qa import (
    Nodes,
    Routes, 
    IntentType
)
from utils import Logger

logger = Logger(__name__)

class ActionRouterNode:
    def __init__(
        self,
    ) -> None:
        pass
    
    def __call__(self, state: QAState) -> QAState:
        logger.info("[NODE] ActionRouterNode")
        current_intent = state.get(StateKeys.CURRENT_INTENT)

        if current_intent == IntentType.APPOINTMENT_INFORMATION:
            route = Routes.INTENT_WAIT

        elif current_intent == IntentType.CONFIRM_APPOINTMENT:
            route = Routes.INTENT_CONFIRM

        elif current_intent == IntentType.CANCEL_APPOINTMENT:
            route = Routes.INTENT_CANCEL

        elif current_intent == IntentType.LIST_APPOINTMENTS:
            route = Routes.INTENT_LIST
        
        logger.info(f"[NODE] ActionRouterNode: router -> {route}")
        state[StateKeys.ROUTE] = route
        state[StateKeys.CURRENT_NODE] = Nodes.ACTION_ROUTER
        
        return state

