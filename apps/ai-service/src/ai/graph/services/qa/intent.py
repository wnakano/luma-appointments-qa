from typing import Any, Dict, List, Optional

from ...models.qa import UserIntent
from ...prompts.templates import QAMessages
from ...prompts.builder.prompt_builder import MessageTypes
from ..llm import LLMService

from utils import Logger

logger = Logger(__name__)


class IntentService(LLMService):
	def __init__(
		self, 
		model: str = "gpt-4o-mini",
		temp: float = 0.0,
	) -> None:
		super().__init__(model=model, temp=temp)

	def run(
		self, 
		user_message: str, 
		verification_step: str, 
		history: List[str]
	) -> UserIntent:
		
		system_prompt = QAMessages.intent_system
		human_prompt = QAMessages.intent_human

		template = self.build_prompt_template(
			system_prompt=system_prompt,
			human_prompt=human_prompt,
			system_input_variables=["verification_step", "history"],
			human_input_variables=["user_message"]
		)

		chain = self.build_structured_chain(
			template=template,
			schema=UserIntent
		)

		try:
			result: UserIntent = chain.invoke(
				{
					"user_message": user_message,
					"verification_step": verification_step,
					"history": history[-3:] if history else [],
				}
			)
			logger.info(f"Intent → {result}")
		
		except Exception as e:
			logger.error(f"Intent error for {verification_step}: {e}")
			result =  UserIntent(
				is_providing_info=True,
				is_asking_question=False,
				is_correction=False,
				wants_to_skip=False,
			)
		return result

