
from typing import Any, Dict, Optional


from ...states.qa import QAState
from ...types.qa import IdentificationState
from ...services.qa import ResponseService
from ...types.qa import Nodes, Routes

from utils import Logger

logger = Logger(__name__)


class CheckUserSessionNode:
	def __init__(
		self,
		response_service: ResponseService
	) -> None:
		self.respond = response_service

	def __call__(self, state: QAState) -> QAState:
		logger.info("[NODE] Checking user session")

		user_verified: bool = state.get("user_verified", False)
		collected_info: Dict[str, Any] = state.get("collected_info", {}) or {}
		verification_step: str = state.get("verification_step", "name")
		user_record: Optional[Dict[str, Any]] = state.get("user_info_db")
		state["current_node"] = Nodes.CHECK_USER_SESSION 
		
		logger.info(
			f"Check user session - verified={user_verified}, collected={list(collected_info.keys())}, user_record={user_record}, step={verification_step}"
		)
		if user_record:
			state["route"] = Routes.IDENTIFIED
			# state["assistant_message"] = "Welcome back!"
			return state
		
		if user_verified:
			context = {
				"action": "welcome_back", 
				"user_name": collected_info.get("name", "User"), 
				"verified": True
			}
			message = self.respond.run(context)

			state["route"] = Routes.VERIFIED
			state["messages"] = state.get("messages", []) + [message]

			return state

		if not collected_info:
			context = {
				"action": "start_verification", 
				"has_previous_info": False
			}
		else:
			context = {
				"action": "continue_verification",
				"has_previous_info": True,
				"collected_so_far": list(collected_info.keys()),
				"next_step": verification_step,
			}
		message = self.respond.run(context)
		
		state["route"] = Routes.MISSING
		state["messages"] = state.get("messages", []) + [message]
		
		return state    





