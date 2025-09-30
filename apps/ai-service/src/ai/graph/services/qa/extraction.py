from typing import Any, Dict, Optional

from ...models.qa import (
	ExtractedInfo, 
	ValidationResult, 
	UserIntent
)
from ...prompts.templates import QAMessages
from ...prompts.builder.prompt_builder import MessageTypes
from ..llm import LLMService


from utils import Logger

logger = Logger(__name__)


class ExtractionService(LLMService):
	_DISPATCH = {
		"name": QAMessages.extraction_name_system,
		"phone": QAMessages.extraction_phone_system,
		"dob": QAMessages.extraction_dob_system,
	}


	def __init__(
		self, 
		model: str = "gpt-4o-mini",
		temp: float = 0.0,
	) -> None:
		super().__init__(model=model, temp=temp)
		
	def run(
		self, 
		user_message: str, 
		info_type: str, 
		collected_info: Dict[str, Any]
	) -> ExtractedInfo:
		
		extraction_prompt = self._DISPATCH.get(info_type, "Extract the provided information.")
		extraction_prompt_formatted = extraction_prompt.format(name=collected_info.get("name", "Unknown"))

		system_prompt = QAMessages.extraction_information_system.format(extraction_prompt=extraction_prompt_formatted)
		human_prompt = QAMessages.extraction_information_human
		
		template = self.build_prompt_template(
			system_prompt=system_prompt,
			human_prompt=human_prompt,
			system_input_variables=[],
			human_input_variables=["user_message"]
		)
		
		chain = self.build_structured_chain(
			template=template,
			schema=ExtractedInfo
		)

		try:
			result: ExtractedInfo = chain.invoke({"user_message": user_message})
			# logger.info(f"Extraction[{info_type}] → {result}")

		except Exception as e:
			logger.error(f"Extraction error for {info_type}: {e}")
			result = ExtractedInfo(
				has_relevant_info=False,
				extracted_value=None,
				confidence=0.0,
				requires_clarification=True,
				clarification_message=f"I couldn't understand that. Could you please provide your {info_type}?",
			)
			
		return result

