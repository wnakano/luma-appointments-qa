from typing import Dict, Optional
from ...states.conversational_qa import QAState, StateKeys
from ...types.conversational_qa import (
	Nodes,
	Routes, 
	IntentType
)
from utils import Logger

logger = Logger(__name__)


class ActionRouterNode:
	INTENT_ROUTE_MAP: Dict[IntentType, Routes] = {
		IntentType.APPOINTMENT_INFORMATION: Routes.INTENT_WAIT,
		IntentType.CONFIRM_APPOINTMENT: Routes.INTENT_CONFIRM,
		IntentType.CANCEL_APPOINTMENT: Routes.INTENT_CANCEL,
		IntentType.LIST_APPOINTMENTS: Routes.INTENT_LIST,
	}
	DEFAULT_ROUTE = Routes.INTENT_WAIT
	
	def __call__(self, state: QAState) -> QAState:
		try:
			logger.info("[NODE] ActionRouterNode")
			
			current_intent = state.get(StateKeys.CURRENT_INTENT)
			
			route = self._get_route_for_intent(current_intent)
			
			state[StateKeys.ROUTE] = route
			state[StateKeys.CURRENT_NODE] = Nodes.ACTION_ROUTER
			
			logger.info(f" ... Routed intent '{current_intent}' to '{route}'")
			
			return state
			
		except Exception as e:
			logger.error(f"Error in ActionRouterNode: {e}", exc_info=True)
			raise
	
	def _get_route_for_intent(self, intent: Optional[IntentType]) -> Routes:
		if intent is None:
			logger.warning("Current intent is None, using default route")
			return self.DEFAULT_ROUTE
		
		route = self.INTENT_ROUTE_MAP.get(intent)
		
		if route is None:
			logger.warning(
				f"Unhandled intent type '{intent}', using default route. "
				f"Supported intents: {list(self.INTENT_ROUTE_MAP.keys())}"
			)
			return self.DEFAULT_ROUTE
		
		return route