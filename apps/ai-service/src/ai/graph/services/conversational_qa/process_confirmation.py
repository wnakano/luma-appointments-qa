from langchain.prompts import PromptTemplate 
from typing import Any, Dict, List, Optional

from ...models.conversational_qa import (
	AppointmentRecordModel, 
	UserIntentModel,
	VerificationRecordModel
	
)
from ...types.conversational_qa import (
    IntentType, 
    ConfirmationIntent,
    Routes
)
from ...states.conversational_qa import QAState	
from ...models.conversational_qa import AppointmentConfirmationResponse
from ...prompts.templates.conversational_qa import ConversationalQAMessages
from ..llm import LLMService

from utils import Logger

logger = Logger(__name__)



class ProcessConfirmationService(LLMService):
	def __init__(
		self, 
		model: str = "gpt-4o-mini",
		temp: float = 0.0,
	) -> None:
		super().__init__(model=model, temp=temp)

	def run(
		self,
		user_message: str,
	) -> AppointmentConfirmationResponse:
		logger.info("[SERVICE] AskConfirmationService")
		system_prompt = ConversationalQAMessages.process_confirmation_system
		human_prompt = ConversationalQAMessages.process_confirmation_human
		
		template = self.build_prompt_template(
			system_prompt=system_prompt,
			human_prompt=human_prompt,
			system_input_variables=[],
			human_input_variables=["user_message"]
		)

		chain = self.build_structured_chain(
			template=template,
			schema=AppointmentConfirmationResponse
		)

		try:
			result = chain.invoke(
				{
					"user_message": user_message
				}
			)
			return result
		except Exception as e:
			logger.error(f"[Service] Intent ERROR: {e}")
			return self._get_fallback(user_message=user_message)


	def _get_fallback(self, user_message: str) -> AppointmentConfirmationResponse:
		"""
		Return a safe fallback intent when classification fails.
		
		Args:
			user_message: The original user message
			
		Returns:
			ConversationIntent with GENERAL_QA intent and low confidence
		"""
		logger.warning("Returning fallback: GENERAL_QA")
		
		return AppointmentConfirmationResponse(
			intent=ConfirmationIntent.UNCLEAR,
			confidence=0.0,
			reasoning="",
			extracted_concerns=""
		)


