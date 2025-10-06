from langchain.prompts import PromptTemplate 
from typing import Any, Dict, List, Optional

from ...models.conversational_qa import ConversationIntentModel, UserIntentModel
from ...types.conversational_qa import IntentType, Routes
from ...states.conversational_qa import QAState	
from ...prompts.templates.conversational_qa import ConversationalQAMessages
from ..llm import LLMService

from utils import Logger

logger = Logger(__name__)


class IntentService(LLMService):
	INTENT_DESCRIPTIONS = {
		IntentType.GENERAL_QA: "General questions about the clinic, hours, services, etc.",
		IntentType.LIST_APPOINTMENTS: "User wants to see their appointments",
		IntentType.CONFIRM_APPOINTMENT: "User wants to confirm an existing appointment",
		IntentType.CANCEL_APPOINTMENT: "User wants to cancel an appointment",
		IntentType.USER_INFORMATION: "User is just sharing his information",
		IntentType.APPOINTMENT_INFORMATION: "User is just sharing appointment information without any action"
	}

	def __init__(
		self, 
		model: str = "gpt-4o-mini",
		temp: float = 0.0,
	) -> None:
		super().__init__(model=model, temp=temp)

	def run(
		self, 
		state: QAState,
	) -> ConversationIntentModel:
		logger.info("[SERVICE] IntentService")

		user_message = state.get("user_message")

		template = self._build_prompt_template(state=state)

		chain = self.build_structured_chain(
			template=template,
			schema=ConversationIntentModel
		)
		intent_list = "\n".join([f"- {k.value}: {v}" for k, v in self.INTENT_DESCRIPTIONS.items()])
		try:
			result: ConversationIntentModel = chain.invoke(
				{
					"intent_list": intent_list,
					"user_message": user_message
				}
			)
			# logger.info(f"Intent → {result}")

			return result
		
		except Exception as e:
			logger.error(f"[Service] Intent ERROR: {e}")
			return self._get_fallback_intent(user_message=user_message)

	def _build_prompt_template(
		self,
		state: QAState
	) -> PromptTemplate:
		
		user_message = state.get("user_message")
		
		system_prompt = ConversationalQAMessages.base_intent_system
		instructions_system = ConversationalQAMessages.base_intent_instructions_system
		human_prompt = ConversationalQAMessages.base_intent_human

		
		route = state.get("route")

		if not state.get("is_verified"):
			system_prompt += ConversationalQAMessages.verification_intent_system
			instructions_system += ConversationalQAMessages.verification_instruction_system
		
		system_prompt += instructions_system

		template = self.build_prompt_template(
			system_prompt=system_prompt,
			human_prompt=human_prompt,
			system_input_variables=["intent_list"],
			human_input_variables=["user_message"]
		)

		return template


	def _get_fallback_intent(self, user_message: str) -> ConversationIntentModel:
		"""
		Return a safe fallback intent when classification fails.
		
		Args:
			user_message: The original user message
			
		Returns:
			ConversationIntent with GENERAL_QA intent and low confidence
		"""
		logger.warning("Returning fallback intent: GENERAL_QA")
		
		return ConversationIntentModel(
			user_intent=UserIntentModel(
				intent_type=IntentType.GENERAL_QA,
				confidence=0.0
			),
			verification_info=None,
			appointment_info=None,
			raw_query=user_message
		)
