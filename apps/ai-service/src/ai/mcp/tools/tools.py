import json
from typing import Any
from langchain.tools import BaseTool
from pydantic import Field
from fastmcp import Client

from .wrapper import MCPExecutor
from utils import Logger

logger = Logger(__name__)


class MCPTool(BaseTool):
	"""LangChain tool wrapper for MCP tools"""
	
	mcp_client: Client = Field(exclude=True)
	tool_name: str
	tool_description: str
	executor: MCPExecutor = Field(exclude=True)

	def __init__(
		self, 
		mcp_client: Any, 
		tool_name: str, 
		tool_description: str, 
		executor: MCPExecutor,
		**kwargs
	) -> None:
		super().__init__(
			name=tool_name,
			description=tool_description,
			mcp_client=mcp_client,
			tool_name=tool_name,
			tool_description=tool_description,
			executor=executor,
			**kwargs
		)
	
	def _run(self, tool_input: str, **kwargs) -> str:
		"""Synchronous wrapper for async MCP tools."""
		return self.executor.sync_wrapper(tool_input)
	
	async def _arun(self, tool_input: str, **kwargs) -> str:
		"""Execute the MCP tool asynchronously"""
		return await self.executor.coroutine(tool_input)