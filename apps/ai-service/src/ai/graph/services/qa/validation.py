

from typing import Any, Dict, Optional

from ...models.qa import ValidationResult
from ...prompts.templates import QAMessages
from ...prompts.builder.prompt_builder import MessageTypes
from ..llm import LLMService

from utils import Logger

logger = Logger(__name__)


class ValidationService(LLMService):

	_DISPATCH = {
		"name": QAMessages.validation_name_system,
		"phone": QAMessages.validation_phone_system,
		"dob": QAMessages.validation_dob_system,
	}

	def __init__(
		self, 
		model: str = "gpt-4o-mini",
		temp: float = 0.0,
	) -> None:
		super().__init__(model=model, temp=temp)

	def run(
		self, 
		value: str, 
		info_type: str
	) -> ValidationResult:
		validation_prompt = self._DISPATCH.get(info_type, "Validate the provided information.").format(value=value)
		system_prompt = QAMessages.validation_information_system.format(validation_prompt=validation_prompt)
		human_prompt = QAMessages.validation_information_human

		template = self.build_prompt_template(			
			system_prompt=system_prompt,
			human_prompt=human_prompt,
			system_input_variables=[],
			human_input_variables=["value"]
		)
		chain = self.build_structured_chain(
			template=template,
			schema=ValidationResult
		)

		try:
			result: ValidationResult = chain.invoke({"value": value})
		
		except Exception as e:
			logger.error(f"Validation error for {info_type}: {e}")
			result = ValidationResult(
				is_valid=False,
				cleaned_value=None,
				error_message=f"Could not validate the {info_type}",
				suggestions=[],
			)
		
		return result