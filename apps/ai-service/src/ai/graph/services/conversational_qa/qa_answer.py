from langchain.prompts import PromptTemplate 

from ...types.conversational_qa import IntentType, Routes
from ...states.conversational_qa import QAState	
from ...models.conversational_qa import QAAnswerModel
from ...prompts.templates.conversational_qa import ConversationalQAMessages
from ..llm import LLMService

from utils import Logger

logger = Logger(__name__)


class QAAnswerService(LLMService):

	def __init__(
		self, 
		model: str = "gpt-4o-mini",
		temp: float = 0.0,
	) -> None:
		super().__init__(model=model, temp=temp)

	def run(
		self, 
		state: QAState,
	) -> QAAnswerModel:
		logger.info("[SERVICE] QAAnswerService")

		user_message = state.get("user_message")
		system_prompt = ConversationalQAMessages.qa_system
		human_prompt = ConversationalQAMessages.qa_human

		template = self.build_prompt_template(
			system_prompt=system_prompt,
			human_prompt=human_prompt,
			system_input_variables=[],
			human_input_variables=['user_message']
		)

		chain = self.build_structured_chain(
			template=template,
			schema=QAAnswerModel
		)
		
		try:
			result: QAAnswerModel = chain.invoke(
				{
					"user_message": user_message
				}
			)
			return result
		
		except Exception as e:
			logger.error(f"[Service] Intent ERROR: {e}")
			return self._get_fallback(user_message=user_message)

	def _build_prompt_template(
		self,
		state: QAState
	) -> PromptTemplate:
		
		user_message = state.get("user_message")
		
		system_prompt = ConversationalQAMessages.intent_system
		instructions_system = ConversationalQAMessages.base_intent_instructions_system
		
		human_prompt = ConversationalQAMessages.intent_human
		
		route = state.get("route")

		if not state.get("is_verified"):
			system_prompt += ConversationalQAMessages.verification_intent_system
			instructions_system += ConversationalQAMessages.verification_instruction_system

		template = self.build_prompt_template(
			system_prompt=system_prompt,
			human_prompt=human_prompt,
			system_input_variables=["intent_list"],
			human_input_variables=["user_message"]
		)

		return template


	def _get_fallback(self, user_message: str) -> QAAnswerModel:
		"""
		Return a safe fallback intent when classification fails.
		
		Args:
			user_message: The original user message
			
		Returns:
			ConversationIntent with GENERAL_QA intent and low confidence
		"""
		logger.warning("Returning fallback: GENERAL_QA")
		
		return QAAnswerModel(
			system_answer="QA failed to generate an answer."
		)
