from typing import Any, Dict, Union, Optional, List

from .base import ArgumentParser


class TodoWriteParser(ArgumentParser):
	"""Parser for todo write operations"""
	
	def parse(self, raw_input: str, parsed_json: Optional[Union[Dict, List]]) -> Dict[str, Any]:
		if isinstance(parsed_json, list):
			return {"todos": parsed_json}
		elif isinstance(parsed_json, dict) and "todos" in parsed_json:
			return {"todos": parsed_json["todos"]}
		else:
			split = [ln.strip() for ln in str(raw_input).splitlines() if ln.strip()]
			todos = [{"content": c, "status": "pending"} for c in split]
			return {"todos": todos}


class TodoUpdateParser(ArgumentParser):
	"""Parser for todo update operations"""
	
	def parse(self, raw_input: str, parsed_json: Optional[Union[Dict, List]]) -> Dict[str, Any]:
		if isinstance(parsed_json, dict):
			return parsed_json
		else:
			raise ValueError("update_todo requires JSON input {id:..., status:...}")
