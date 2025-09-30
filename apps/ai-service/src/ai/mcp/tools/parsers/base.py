
from typing import Any, Dict, Union, Optional, List
from abc import ABC, abstractmethod


class ArgumentParser(ABC):
	"""Abstract base class for tool-specific argument parsers"""
	@abstractmethod
	def parse(self, raw_input: str, parsed_json: Optional[Union[Dict, List]]) -> Dict[str, Any]:
		pass

