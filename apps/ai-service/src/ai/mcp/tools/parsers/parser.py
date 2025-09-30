import threading
from typing import Any, Dict, Union, Optional, List

from ..schema import ToolSchema
from .base import ArgumentParser


class DefaultParser(ArgumentParser):
	"""Default parser for generic tools"""
	
	def parse(self, raw_input: str, parsed_json: Optional[Union[Dict, List]]) -> Dict[str, Any]:
		return parsed_json if isinstance(parsed_json, dict) else {"input": raw_input}


class EmptyArgsParser(ArgumentParser):
	"""Parser for tools that don't require arguments"""
	
	def parse(self, raw_input: str, parsed_json: Optional[Union[Dict, List]]) -> Dict[str, Any]:
		return {}


class SchemaBasedParser(ArgumentParser):
	"""Parser that uses FastMCP tool schema for validation"""
	
	def __init__(self, tool_schema: ToolSchema):
		self.schema = tool_schema
	
	def parse(self, raw_input: str, parsed_json: Optional[Union[Dict, List]]) -> Dict[str, Any]:
		if isinstance(parsed_json, dict):
			# Validate against schema
			args = {}
			for param in self.schema.required_params:
				if param not in parsed_json:
					raise ValueError(f"Missing required parameter: {param}")
				args[param] = parsed_json[param]
			
			for param in self.schema.optional_params:
				if param in parsed_json:
					args[param] = parsed_json[param]
			
			return args
		else:
			# Handle empty input for tools with no required parameters
			if not self.schema.required_params:
				# Tool has no required params - handle empty input gracefully
				if not raw_input or raw_input.strip() == "":
					return {}
				# For non-empty input, try to map to first optional parameter
				elif self.schema.optional_params:
					first_optional = self.schema.optional_params[0]
					return {first_optional: str(raw_input)}
				else:
					return {}
			
			# Tool has required parameters
			elif len(self.schema.required_params) == 1:
				# Single required parameter - map input to it
				if not raw_input or raw_input.strip() == "":
					raise ValueError(f"Missing required parameter: {self.schema.required_params[0]}")
				return {self.schema.required_params[0]: str(raw_input)}
			else:
				# Multiple required parameters - need structured input
				raise ValueError(f"Tool {self.schema.name} requires structured input with parameters: {', '.join(self.schema.required_params)}")


class ParseStrategy:
	"""Registry for tool parsers"""
	
	_parsers: Dict[str, ArgumentParser] = {}
	_lock = threading.Lock()
	
	@classmethod
	def register(cls, tool_name: str, parser: ArgumentParser):
		"""Register a parser for a specific tool"""
		with cls._lock:
			cls._parsers[tool_name] = parser
	
	@classmethod
	def get_parser(cls, tool_name: str) -> ArgumentParser:
		"""Get parser for a tool, returns default if not found"""
		return cls._parsers.get(tool_name, DefaultParser())
	
	@classmethod
	def register_from_schema(cls, tool_schema: ToolSchema):
		"""Register a schema-based parser from FastMCP tool schema"""
		parser = SchemaBasedParser(tool_schema)
		cls.register(tool_schema.name, parser)