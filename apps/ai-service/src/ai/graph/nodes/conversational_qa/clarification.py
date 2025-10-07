from typing import List, Dict, Optional

from ...states.conversational_qa import QAState, StateKeys
from ...types.conversational_qa import (
	Nodes,
	Routes, 
	MessageKeys
)
from ...models.conversational_qa import VerificationInfoModel, AppointmentInfoModel
from ...services.conversational_qa import ClarificationService
from utils import Logger

logger = Logger(__name__)


class ClarificationNode:
	"""Node for generating clarification prompts."""
	
	def __init__(self, clarification_service: ClarificationService):
		self.clarification_service = clarification_service
	
	def __call__(self, state: QAState) -> QAState:
		try:
			logger.info("[NODE] ClarificationNode")
			
			current_node = state.get(StateKeys.CURRENT_NODE)
			route = state.get(StateKeys.ROUTE)
			user_message = state.get(StateKeys.USER_MESSAGE, "")
			messages = state.get(StateKeys.MESSAGES, [])

			conversation_context = self._build_conversation_context(messages)
			if current_node == Nodes.VERIFICATION_PATIENT:
				verification_info = state.get(StateKeys.USER_INFO)
				diagnostic_info = state.get(StateKeys.VERIFICATION_DIAGNOSTICS)
				
				system_prompt = self.clarification_service.user_run(
					verification_info=verification_info,
					diagnostic_info=diagnostic_info,
					conversation_context=conversation_context
				)

				state[StateKeys.VERIFICATION_DIAGNOSTICS] = None
				
			elif current_node == Nodes.VERIFICATION_APPOINTMENT:
				appointment_info = state.get(StateKeys.APPOINTMENT_INFO)
				diagnostic_info = state.get(StateKeys.APPOINTMENT_DIAGNOSTICS)
				
				system_prompt = self.clarification_service.appointment_run(
					appointment_info=appointment_info,
					diagnostic_info=diagnostic_info,
					conversation_context=conversation_context
				)

				state[StateKeys.APPOINTMENT_DIAGNOSTICS] = None
			
			elif route == Routes.INTENT_WAIT and current_node == Nodes.ACTION_ROUTER:
				appointment_info = state.get(StateKeys.APPOINTMENT_INFO)
				system_prompt = self.clarification_service.appointment_wait(
					appointment_info=appointment_info
				)
			
			else:
				logger.warning(f"Unhandled clarification scenario: {current_node}, {route}")
				system_prompt = "Could you please provide more information?"
			
			state[StateKeys.CURRENT_NODE] = Nodes.CLARIFICATION
			state[StateKeys.MESSAGES] = messages + [
				{
					MessageKeys.USER_MESSAGE: user_message,
					MessageKeys.SYSTEM_MESSAGE: system_prompt
				}
			]
			
			logger.info(" ... Clarification prompt generated")
			
			return state
			
		except Exception as e:
			logger.error(f"Error in ClarificationNode: {e}", exc_info=True)
			raise
	
	def _build_conversation_context(self, messages: List[Dict]) -> str:
		"""
		Build conversation context string from message history.
		
		Args:
			messages: List of message dictionaries
			
		Returns:
			Formatted conversation context
		"""
		if not messages:
			return "No previous conversation."
		
		recent_messages = messages[-3:] if len(messages) > 3 else messages
		
		context_parts = []
		for msg in recent_messages:
			if not isinstance(msg, dict):
				continue
			user_msg = msg.get(MessageKeys.USER_MESSAGE, "")
			system_msg = msg.get(MessageKeys.SYSTEM_MESSAGE, "")
			
			if user_msg:
				context_parts.append(f"User: {user_msg}")
			if system_msg:
				context_parts.append(f"Assistant: {system_msg}")
		
		return "\n".join(context_parts)