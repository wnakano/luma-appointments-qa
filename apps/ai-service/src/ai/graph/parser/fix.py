from typing import Any, Dict, Type, TypeVar
from pydantic import BaseModel

from langchain.output_parsers.pydantic import PydanticOutputParser
from langchain.output_parsers.fix import OutputFixingParser


from ..services.llm import LLMService


class FixingParser(LLMService):
	"""
	Factory/manager for OutputFixingParser that can use either OpenAI
	as the 'fixing LLM' to repair malformed JSON into a Pydantic model.
	"""

	def __init__(
		self,
		model: str = "gpt-4o-mini",
		temperature: float = 0.0,
		max_repair_rounds: int = 2,
		**llm_kwargs: Any,
	) -> None:
		super().__init__(model=model, temp=temperature)

		self.max_repair_rounds = int(max_repair_rounds)
		self.llm_kwargs = llm_kwargs

		self._parsers: Dict[Type[BaseModel], OutputFixingParser] = {}

	def parse_to_model(self, raw_text: str, schema_class: Type[BaseModel]) -> Type[BaseModel]:
		"""
		Parse `raw_text` into a Pydantic model `schema_class`,
		auto-repairing malformed outputs via the chosen LLM if needed.
		"""
		parser = self._get_or_build_parser(schema_class)
		parsed = parser.parse(raw_text)  # returns an instance of schema_class
		return parsed

	def parse_to_dict(self, raw_text: str, schema_class: Type[BaseModel]) -> Dict[str, Any]:
		"""
		Parse to a dictionary using the model's .model_dump().
		"""
		model_obj = self.parse_to_model(raw_text, schema_class)
		return model_obj.model_dump()

	def _get_or_build_parser(self, schema_class: Type[BaseModel]) -> OutputFixingParser:
		if schema_class not in self._parsers:
			base_parser = PydanticOutputParser(pydantic_object=schema_class)
			fixing_parser = OutputFixingParser.from_llm(
				llm=self.llm,
				parser=base_parser,
				max_retries=self.max_repair_rounds,
			)
			self._parsers[schema_class] = fixing_parser
		return self._parsers[schema_class]
