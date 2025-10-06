from ...states.conversational_qa import QAState
from ...types.conversational_qa import (
	Routes, 
	Nodes,
	IntentType,
	ConfirmationIntent,
	DBAppointmentStatus
)
from utils import Logger

logger = Logger(__name__)


class ActionResponseNode:
	def __init__(
		self,
	) -> None:
		pass
	
	def __call__(self, state: QAState) -> QAState:
		logger.info("[NODE] ActionResponseNode")
		confirmation_result = state.get("confirmation_intent")
		current_intent = state.get("current_intent")
		messages = state.get("messages", [])
		user_message = state.get("user_message")

		if current_intent == IntentType.LIST_APPOINTMENTS:
			system_message = messages[-1]["system_message"]
		else:
			confirmation_intent = confirmation_result.intent
			if confirmation_intent == ConfirmationIntent.CONFIRM:
				system_message = "Your appointment has been "
			elif confirmation_intent == ConfirmationIntent.REJECT:
				system_message = "Your appointment has not been "
			
			if current_intent == IntentType.CANCEL_APPOINTMENT:
				system_message += "canceled."
			elif current_intent == IntentType.CONFIRM_APPOINTMENT:
				system_message += "confirmed."

		system_message += "\nIs there anything else I can do for you?"

		state["messages"] = messages + [
			{
				"user_message": user_message,
				"system_message": system_message
			}
		]
		state["current_node"] = Nodes.ACTION_RESPONSE

		return state

