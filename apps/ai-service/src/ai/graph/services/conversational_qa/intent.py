from langchain.prompts import PromptTemplate 
from typing import Dict, Optional

from ...models.conversational_qa import ConversationIntentModel, UserIntentModel
from ...types.conversational_qa import IntentType
from ...states.conversational_qa import QAState, StateKeys
from ...prompts.templates.conversational_qa import ConversationalQAMessages
from ..llm import LLMService
from utils import Logger

logger = Logger(__name__)


class IntentService(LLMService):
	INTENT_DESCRIPTIONS: Dict[IntentType, str] = {
		IntentType.GENERAL_QA: "General questions about the clinic, hours, services, etc.",
		IntentType.LIST_APPOINTMENTS: "User wants to see their appointments",
		IntentType.CONFIRM_APPOINTMENT: "User wants to confirm an existing appointment",
		IntentType.CANCEL_APPOINTMENT: "User wants to cancel an appointment",
		IntentType.USER_INFORMATION: "User is sharing their personal information",
		IntentType.APPOINTMENT_INFORMATION: "User is sharing appointment information without requesting any action"
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
		try:
			logger.info("[SERVICE] IntentService")
			
			user_message = state.get(StateKeys.USER_MESSAGE, "")
			
			if not user_message or not user_message.strip():
				logger.warning("Empty user message, returning fallback intent")
				return self._get_fallback_intent(user_message)
			
			template = self._build_prompt_template(state=state)
			
			chain = self.build_structured_chain(
				template=template,
				schema=ConversationIntentModel
			)
			
			intent_list = self._format_intent_list()
			
			result: ConversationIntentModel = chain.invoke({
				"intent_list": intent_list,
				"user_message": user_message
			})

			intent_type = result.user_intent.intent_type
			confidence = result.user_intent.confidence
			logger.info(
				f" ... Classified intent: {intent_type} "
				f"(confidence: {confidence:.2f})"
			)
			
			return result
			
		except Exception as e:
			logger.error(f"[SERVICE] IntentService ERROR: {e}", exc_info=True)
			user_message = state.get(StateKeys.USER_MESSAGE, "")
			return self._get_fallback_intent(user_message)
	
	def _build_prompt_template(self, state: QAState) -> PromptTemplate:
		system_prompt = ConversationalQAMessages.base_intent_system
		instructions_system = ConversationalQAMessages.base_intent_instructions_system
		human_prompt = ConversationalQAMessages.base_intent_human
		
		is_verified = state.get(StateKeys.IS_VERIFIED, False)
		
		if not is_verified:
			logger.info(" ... Adding verification context to intent prompt")
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
	
	def _format_intent_list(self) -> str:
		intent_lines = [
			f"- {intent.value}: {description}"
			for intent, description in self.INTENT_DESCRIPTIONS.items()
		]
		return "\n".join(intent_lines)
	
	def _get_fallback_intent(self, user_message: str) -> ConversationIntentModel:
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