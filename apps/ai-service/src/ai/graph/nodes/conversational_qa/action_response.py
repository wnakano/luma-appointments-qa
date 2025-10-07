from ...states.conversational_qa import QAState, StateKeys
from ...types.conversational_qa import (
	Nodes,
	IntentType,
	ConfirmationIntent
)
from ...models.conversational_qa import AppointmentConfirmationResponse
from utils import Logger

logger = Logger(__name__)


class ActionResponseNode:
	CONFIRMATION_MESSAGES = {
		(IntentType.CANCEL_APPOINTMENT, ConfirmationIntent.CONFIRM): "Your appointment has been canceled.",
		(IntentType.CANCEL_APPOINTMENT, ConfirmationIntent.REJECT): "Your appointment has not been canceled.",
		(IntentType.CONFIRM_APPOINTMENT, ConfirmationIntent.CONFIRM): "Your appointment has been confirmed.",
		(IntentType.CONFIRM_APPOINTMENT, ConfirmationIntent.REJECT): "Your appointment has not been confirmed.",
	}
	
	FOLLOW_UP_MESSAGE = "\n\nIs there anything else I can do for you?"
	
	def __call__(self, state: QAState) -> QAState:
		try:
			logger.info("[NODE] ActionResponseNode")
			
			current_intent = state.get(StateKeys.CURRENT_INTENT)
			user_message = state.get(StateKeys.USER_MESSAGE, "")
			messages = state.get(StateKeys.MESSAGES, [])
			
			system_message = self._generate_system_message(state, current_intent)
			
			state[StateKeys.MESSAGES] = messages + [
				{
					"user_message": user_message,
					"system_message": system_message
				}
			]
			state[StateKeys.CURRENT_NODE] = Nodes.ACTION_RESPONSE
			
			logger.info(f" ... Generated response for intent: {current_intent}")
			
			return state
			
		except Exception as e:
			logger.error(f"Error in ActionResponseNode: {e}", exc_info=True)
			raise
	
	def _generate_system_message(
		self, 
		state: QAState, 
		current_intent: IntentType
	) -> str:
		if current_intent == IntentType.LIST_APPOINTMENTS:
			return self._get_list_appointments_message(state)
		
		elif current_intent in {IntentType.CANCEL_APPOINTMENT, IntentType.CONFIRM_APPOINTMENT}:
			return self._get_confirmation_message(state, current_intent)
		
		else:
			logger.warning(f"Unhandled intent type in ActionResponseNode: {current_intent}")
			return "I've processed your request." + self.FOLLOW_UP_MESSAGE
	
	def _get_list_appointments_message(self, state: QAState) -> str:
		messages = state.get(StateKeys.MESSAGES, [])
		
		if not messages:
			logger.warning("No messages found for LIST_APPOINTMENTS intent")
			return "No appointments found." + self.FOLLOW_UP_MESSAGE
		
		last_message = messages[-1]
		system_message = last_message.get("system_message", "")
		
		if not system_message:
			logger.warning("No system_message in last message for LIST_APPOINTMENTS")
			return "Here are your appointments." + self.FOLLOW_UP_MESSAGE
		
		# Add follow-up question if not already present
		if self.FOLLOW_UP_MESSAGE.strip() not in system_message:
			system_message += self.FOLLOW_UP_MESSAGE
		
		return system_message
	
	def _get_confirmation_message(
		self, 
		state: QAState, 
		current_intent: IntentType
	) -> str:
		confirmation_result: AppointmentConfirmationResponse = state.get(
			StateKeys.CONFIRMATION_INTENT
		)
		
		if not confirmation_result:
			logger.error("No confirmation_result found in state")
			return "Unable to process your request." + self.FOLLOW_UP_MESSAGE
		
		confirmation_intent = confirmation_result.intent
		
		message_key = (current_intent, confirmation_intent)
		system_message = self.CONFIRMATION_MESSAGES.get(
			message_key,
			"Your request has been processed."
		)
		
		if message_key not in self.CONFIRMATION_MESSAGES:
			logger.warning(
				f"No message template for intent: {current_intent}, "
				f"confirmation: {confirmation_intent}"
			)
		
		return system_message + self.FOLLOW_UP_MESSAGE