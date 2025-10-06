from ...states.conversational_qa import QAState
from ...types.conversational_qa import (
	Nodes,
	Routes, 
	IntentType
)
from ...services.conversational_qa import ClarificationService
from utils import Logger

logger = Logger(__name__)



class ClarificationNode:
	def __init__(
		self,
		clarification_service: ClarificationService,
	) -> None:
		self.clarification_service = clarification_service

	def __call__(self, state: QAState) -> QAState:
		logger.info("[NODE] ClarificationNode")
		current_node = state.get("current_node")
		route = state.get("route")
		user_message = state.get("user_message")
		messages = state.get("messages")

		if current_node == Nodes.VERIFICATION_PATIENT:
			verification_info = state.get("verification_info", None)
			system_prompt = self.clarification_service.user_run(
				verification_info=verification_info
			)
			# state["appointment_request_counter"] += 1

		if current_node == Nodes.VERIFICATION_APPOINTMENT:
			appointment_info = state.get("appointment_info", None)
			system_prompt = self.clarification_service.appointment_run(
				appointment_info=appointment_info
			)
			# state["user_request_counter"] += 1
		if route == Routes.INTENT_WAIT and current_node == Nodes.ACTION_ROUTER:
			system_prompt = self.clarification_service.appointment_wait(
				appointment_info=appointment_info
			)

		state["current_node"] = Nodes.CLARIFICATION
		state["messages"] = messages + [
			{
				"user_message": user_message,
				"system_message": system_prompt
			}
		]

		return state

