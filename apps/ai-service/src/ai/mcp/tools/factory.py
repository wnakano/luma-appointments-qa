
import json
from typing import Any, Dict
from langchain.tools import BaseTool
from pydantic import Field
from mcp.types import Tool
from typing import List

from .tools import MCPTool
from .wrapper import MCPExecutor

from utils import Logger


class MCPToolFactory:
	"""Factory class to create MCP tools from server configuration"""
	
	@staticmethod
	def create_tools_from_config(
		mcp_client: Any, 
		tools_list: List[Any]
	) -> List[Tool]:
		"""
		Create a list of MCPTool instances from FastMCP tools list.
		
		Args:
			mcp_client: The MCP client instance
			tools_list: List of Tool objects from FastMCP client
			
		Returns:
			List of MCPTool instances
		"""
		mcp_tools = []
		
		for tool in tools_list:
			tool_name = tool.name
			tool_description = tool.description or f"{tool_name} tool"
			executor = MCPExecutor.from_fastmcp_tool(mcp_client, tool)
			mcp_tool = MCPTool(
				mcp_client=mcp_client,
				tool_name=tool_name,
				tool_description=tool_description,
				executor=executor
			)
			mcp_tools.append(mcp_tool)
		
		return mcp_tools