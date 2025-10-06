from ...states.conversational_qa import QAState, StateKeys
from ...types.conversational_qa import (
	Nodes,
	IntentType,
	ConfirmationIntent,
	MessageKeys,
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
		confirmation_result = state.get(StateKeys.CONFIRMATION_INTENT)
		current_intent = state.get(StateKeys.CURRENT_INTENT)
		messages = state.get(StateKeys.MESSAGES, [])
		user_message = state.get(StateKeys.USER_MESSAGE)

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

		state[StateKeys.MESSAGES] = messages + [
			{
				MessageKeys.USER_MESSAGE: user_message,
				MessageKeys.SYSTEM_MESSAGE: system_message
			}
		]
		state[StateKeys.CURRENT_NODE] = Nodes.ACTION_RESPONSE

		return state

