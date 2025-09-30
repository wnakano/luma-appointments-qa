from typing import Any, Dict, Union, Optional, List

from .base import ArgumentParser
from utils import Logger

logger = Logger(__name__)


class DatabaseQueryParser(ArgumentParser):
	"""Parser for database query tools"""
	
	def parse(self, raw_input: str, parsed_json: Optional[Union[Dict, List]]) -> Dict[str, Any]:
		if isinstance(parsed_json, dict):
			return {
				"query": parsed_json.get("query", ""),
				"params": parsed_json.get("params", [])
			}
		return {"query": str(raw_input), "params": []}


class DatabaseSchemaParser(ArgumentParser):
	"""Parser for database schema tool"""
	
	def parse(self, raw_input: str, parsed_json: Optional[Union[Dict, List]]) -> Dict[str, Any]:
		if isinstance(parsed_json, dict):
			return {"table_name": parsed_json.get("table_name")}
		elif raw_input == "" or (isinstance(raw_input, str) and raw_input.lower() in {"all", "*"}):
			return {}
		else:
			return {"table_name": str(raw_input)}


class DatabaseTransactionParser(ArgumentParser):
	"""Parser for database transaction tool"""
	
	def parse(self, raw_input: str, parsed_json: Optional[Union[Dict, List]]) -> Dict[str, Any]:
		if isinstance(parsed_json, list):
			return {"queries": parsed_json}
		elif isinstance(parsed_json, dict) and "queries" in parsed_json:
			return {"queries": parsed_json["queries"]}
		else:
			raise ValueError('db_transaction expects JSON array or {"queries": [...]}.')

