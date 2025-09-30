from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class ToolSchema:
	"""Represents a tool's input schema"""
	name: str
	required_params: List[str]
	optional_params: List[str]
	param_types: Dict[str, Any]

