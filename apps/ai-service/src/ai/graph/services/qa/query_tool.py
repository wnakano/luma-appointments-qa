
import os
import json


from fastmcp import Client
# from langchain.agents import (
# 	AgentExecutor, 
# 	create_react_agent
# )
from langgraph.prebuilt.chat_agent_executor import AgentState
from langgraph.prebuilt import create_react_agent

from langchain_core.prompts import ChatPromptTemplate
from typing import (
	Any, 
	Dict, 
	Optional
)

from ...models.qa import (
	ExtractedUserInfo, 
	UserValidationResult, 
	UserIntent
)
from ...prompts.templates import QAMessages
from ...prompts.builder.prompt_builder import MessageTypes
from ..llm import LLMService
from ai.mcp.client import MCPClientManager
from ...parser.fix import FixingParser

from utils import Logger

logger = Logger(__name__)


class UserSearchAgentState(AgentState):
	user_name: str
	user_birthday: str
	user_phone: str
	search_context: str
	structured_response: UserValidationResult


class QueryToolService(LLMService):
	"""Service for finding and retrieving exact user matches from database using MCP tools"""


	def __init__(
		self, 
		model: str = "gpt-4o-mini",
		temp: float = 0.0,
	) -> None:
		super().__init__(model=model, temp=temp)
		self.mcp_server_url = os.getenv("MCP_SERVER_URL", "http://mcp-server:8080/mcp")
		self.fixing_parser = FixingParser(model=model, temperature=temp, max_repair_rounds=2)
		
	async def find_user(
		self, 
		user_info: ExtractedUserInfo,
		# intent: UserIntent
	) -> UserValidationResult:
		"""
		Find exact user match in database and return complete user record
		
		Args:
			user_info: Extracted user information (name, birthday, phone)
			intent: User intent for context
			
		Returns:
			UserValidationResult with found user data or validation failure details
		"""
		try:
			async with MCPClientManager(self.mcp_server_url) as mcp_manager:
				# First try direct lookup for exact match
				# user_record = await self._find_exact_user_match(mcp_manager, user_info)
				query_user_info = user_info.model_copy(deep=True)
				
				user_record = await self._agent_based_user_search(
					mcp_manager=mcp_manager, 
					user_info=user_info
				) 
				logger.info(f"user_record = {user_record}")
				logger.info(f"query_user_info = {query_user_info}")


				if all([
					user_record.is_valid, 
					len(user_record.patient_id) > 0,
					user_record.phone == query_user_info.phone,
					user_record.date_of_birth == query_user_info.date_of_birth,
				]):
					logger.info("Exact match found")
					return user_record

				logger.info("No exact match found")
				return query_user_info

		except Exception as e:
			logger.error(f"Error in find_user: {e}")
			return UserValidationResult(
				is_valid=False,
				confidence_score=0.0,
				error_message=f"User search error: {str(e)}",
				details={}
			)
	
	async def _agent_based_user_search(
		self, 
		mcp_manager: MCPClientManager,
		user_info: UserValidationResult,
		# intent: UserIntent
	) -> UserValidationResult:
		"""
		Use LLM agent for fuzzy matching when exact match fails
		"""
		try:

			query_system = QAMessages.query_validation_system.format(
				tool_names="db_schema, db_query",
			)

			mcp_tools = await mcp_manager.get_langchain_tools()
			db_tools = [tool for tool in mcp_tools if tool.tool_name in ("db_schema", "db_query")]
			
			agent = create_react_agent(
				model=self.llm,
				tools=db_tools,
				prompt=query_system,
				state_schema=UserSearchAgentState,
				response_format=UserValidationResult,
				debug=False
			)
			
			# Execute the search
			search_input_dict = {
				"user_name": user_info.full_name,
				"user_birthday": user_info.date_of_birth,
				"user_phone": user_info.phone,
			}

			search_input = f"""
			Find the patient using the following information:
			{str(search_input_dict)}
			"""

			input_messages = [{"role": "user", "content": search_input}]
			
			result = await agent.ainvoke({"messages": input_messages})
			structured_response = result.get("structured_response")

			return structured_response
			
		except Exception as e:
			logger.error(f"Error in agent-based user search: {e}")
			return UserValidationResult()
	
	async def find_appointments_by_user_id(
		self, 
		user_info: ExtractedUserInfo,
		# intent: UserIntent
	) -> UserValidationResult:
		"""
		Find exact user match in database and return complete user record
		
		Args:
			user_info: Extracted user information (name, birthday, phone)
			intent: User intent for context
			
		Returns:
			UserValidationResult with found user data or validation failure details
		"""
		try:
			async with MCPClientManager(self.mcp_server_url) as mcp_manager:
				# user_record = await self._find_exact_user_match(mcp_manager, user_info)
				query_user_info = user_info.model_copy(deep=True)
				
				user_record = await self._agent_based_user_search(
					mcp_manager=mcp_manager, 
					user_info=user_info
				) 
				logger.info(f"user_record = {user_record}")
				logger.info(f"query_user_info = {query_user_info}")


				if all([
					user_record.is_valid, 
					len(user_record.patient_id) > 0,
					user_record.phone == query_user_info.phone,
					user_record.date_of_birth == query_user_info.date_of_birth,
				]):
					logger.info("Exact match found")
					return user_record

				logger.info("No exact match found")
				return query_user_info

		except Exception as e:
			logger.error(f"Error in find_user: {e}")
			return UserValidationResult(
				is_valid=False,
				confidence_score=0.0,
				error_message=f"User search error: {str(e)}",
				details={}
			)
		
	async def _find_exact_user_match(
		self, 
		mcp_manager: MCPClientManager, 
		user_info: UserValidationResult
	) -> Optional[Dict[str, Any]]:
		"""
		Find exact user match using direct database queries
		
		Returns:
			Complete user record if found, None otherwise
		"""
		logger.info(f"Searching for user: {user_info.model_dump()}")
		try:
			# Strategy 1: Match all three fields (most restrictive)
			exact_match = await self._query_user_by_all_fields(
				mcp_manager=mcp_manager, 
				user_info=user_info
			)
			if exact_match:
				logger.info(f"Found exact match for user: {user_info.full_name}")
				return exact_match
			
			# Strategy 2: Match by phone + name (phone is usually unique)
			phone_name_match = await self._query_user_by_phone_name(
				mcp_manager=mcp_manager, 
				user_info=user_info
			)
			if phone_name_match:
				logger.info(f"Found match by phone+name for user: {user_info.full_name}")
				return phone_name_match
			
			# Strategy 3: Match by phone only (if phone is unique identifier)
			phone_match = await self._query_user_by_phone(
				mcp_manager=mcp_manager, 
				user_info=user_info
			)
			if phone_match:
				logger.info(f"Found match by phone for user: {user_info.phone_number}")
				return phone_match
				
			return None
			
		except Exception as e:
			logger.error(f"Error in exact user match search: {e}")
			return None
	
	async def _query_user_by_all_fields(
		self, 
		mcp_manager: MCPClientManager, 
		user_info: UserValidationResult
	) -> Optional[Dict[str, Any]]:
		query = """
		SELECT patient_id, full_name, phone, date_of_birth, email
		FROM patients 
		WHERE LOWER(TRIM(full_name)) = LOWER(TRIM($1)) 
		AND phone = $2
		AND date_of_birth = $3
		LIMIT 1
		"""	
		# Convert date to string format for PostgreSQL
		date_str = user_info.date_of_birth.strftime("%Y-%m-%d") if user_info.date_of_birth else None
		
		params = [
			user_info.full_name,
			user_info.phone,
			date_str
		]
		
		result = await mcp_manager.execute_db_query(query, params)
		logger.info(f"[_query_user_by_all_fields] result: {result}")
		
		if result.get("status") == "success" and result.get("data"):
			return result["data"][0]
		return None
	
	async def _query_user_by_phone_name(
		self, 
		mcp_manager: MCPClientManager, 
		user_info: UserValidationResult
	) -> Optional[Dict[str, Any]]:
		"""Query user by phone number and name"""
		query = """
		SELECT patient_id, full_name, phone, date_of_birth, email
		FROM patients 
		WHERE LOWER(TRIM(full_name)) = LOWER(TRIM($1)) 
		AND phone = $2
		LIMIT 1
		"""
		
		params = [user_info.full_name, user_info.phone]
		result = await mcp_manager.execute_db_query(query, params)
		logger.info(f"[_query_user_by_phone_name] result: {result}")
		if result.get("status") == "success" and result.get("data"):
			return result["data"][0]
		return None
	
	async def _query_user_by_phone(
		self, 
		mcp_manager: MCPClientManager, 
		user_info: UserValidationResult
	) -> Optional[Dict[str, Any]]:
		"""Query user by phone number only"""
		query = """
		SELECT patient_id, full_name, phone, date_of_birth, email
		FROM patients 
		WHERE phone = $1
		LIMIT 1
		"""
		
		params = [user_info.phone]
		result = await mcp_manager.execute_db_query(query, params)
		logger.info(f"[_query_user_by_phone] result: {result}")
		if result.get("status") == "success" and result.get("data"):
			return result["data"][0]
		return None
	