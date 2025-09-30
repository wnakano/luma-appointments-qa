from ...prompts.templates import QAMessages
from ..llm import LLMService
from ...states.qa import QAState

from utils import Logger

logger = Logger(__name__)


class ResponseService(LLMService):
	def __init__(
		self, 
		model: str = "gpt-4o-mini",
		temp: float = 0.0,
	) -> None:
		super().__init__(model=model, temp=temp)

	def run(self, context: dict) -> str:
		system_prompt = QAMessages.contextual_information_system
		human_prompt = QAMessages.contextual_information_human
		template = self.build_prompt_template(
			system_prompt=system_prompt,
			human_prompt=human_prompt,
			system_input_variables=[],
			human_input_variables=["context"]
		)
		
		chain = self.build_chain(
			template=template
		)

		result = chain.invoke({"context": context})

		return result.content

	def generate_verification_failed_response(
		self, 
		state: QAState
	) -> str:
		system_prompt = QAMessages.verification_failed_system
		human_prompt = QAMessages.verification_failed_human
		template = self.build_prompt_template(
			system_prompt=system_prompt,
			human_prompt=human_prompt,
			system_input_variables=[],
			human_input_variables=["full_name", "phone", "date_of_birth"]
		)

		chain_input = {}
		collected_info = state.get("collected_info", {}) or {}
		for field, readable_field in zip(['name', 'phone', 'dob'], ['full_name', 'phone', 'date_of_birth']):
			if field not in collected_info or not collected_info[field]:
				chain_input[readable_field] = ""
			else:
				chain_input[readable_field] = collected_info[field]

		chain = self.build_chain(
			template=template
		)

		result = chain.invoke(chain_input)

		return result.content
