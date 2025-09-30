
from typing import Any, Dict, Optional


from ...states.qa import QAState
from ...types.qa import IdentificationState
from ...services.qa import ResponseService
from ...types.qa import Routes, Nodes
from utils import Logger

logger = Logger(__name__)


class CollectUserInfoNode:
	def __init__(
		self, 
		response_service: ResponseService
	) -> None:
		self.response_service = response_service

	def __call__(
		self, 
		state: QAState
	) -> QAState:
		logger.info("[NODE] Collecting user information")

		step: str = state.get("verification_step", "name")
		collected: Dict[str, Any] = state.get("collected_info", {}) or {}

		logger.info(f"Collecting user info - step={step}, collected={list(collected.keys())}")

		context = {
			"action": "request_information",
			"step": step,
			"collected_info": collected,
			"is_first_request": len(collected) == 0,
		}
		message = self.response_service.run(context)

		if step == "complete":
			state["route"] = Routes.VERIFY
		else:
			state["route"] = Routes.PROCESS_USER_INPUT
		
		previous_node = state.get("current_node")
		if previous_node == Nodes.VERIFICATION_FAILED:
			failed_message = state.get("assistant_message", "")
			message = f"{failed_message}\n\n{message}"
			state["assistant_message"] = ""

		state["messages"] = state.get("messages", []) + [message]
		state["current_node"] = Nodes.COLLECT_USER_INFO
		
		return state

