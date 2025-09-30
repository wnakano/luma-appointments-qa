import json
import asyncio
import logging
from typing import Any, Dict, Union, Optional, Protocol, List
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import lru_cache
import threading
import concurrent.futures

from .schema import ToolSchema
from .parsers import (
	ParseStrategy,
	EmptyArgsParser,
	TodoWriteParser,
	TodoUpdateParser,
	DatabaseQueryParser,
	DatabaseSchemaParser,
	DatabaseTransactionParser
)
from utils import Logger

logger = Logger(__name__)


ParseStrategy.register("db_query", DatabaseQueryParser())
ParseStrategy.register("db_write", DatabaseQueryParser())
ParseStrategy.register("db_schema", DatabaseSchemaParser())
ParseStrategy.register("db_transaction", DatabaseTransactionParser())
ParseStrategy.register("write_todos", TodoWriteParser())
ParseStrategy.register("update_todo", TodoUpdateParser())
ParseStrategy.register("read_todos", EmptyArgsParser())


class MCPExecutor:
    """Handles the execution logic for MCP tools with improved error handling and flexibility"""
    
    def __init__(self, mcp_client: Any, tool_name: str, tool_schema: Optional[ToolSchema] = None):
        self.mcp_client = mcp_client
        self.tool_name = tool_name
        self.tool_schema = tool_schema
        
        # Register schema-based parser if provided, but with special handling for known tools
        if tool_schema:
            # Special case for db_schema - always allow empty input
            if tool_name == "db_schema":
                ParseStrategy.register(tool_name, DatabaseSchemaParser())
            else:
                ParseStrategy.register_from_schema(tool_schema)
    
    def sync_wrapper(self, input_str: str) -> str:
        """Synchronous wrapper for async MCP tools."""
        try:
            # Try to get current event loop
            try:
                loop = asyncio.get_running_loop()
                # If we're already in an event loop, create a new one in a thread
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(self._run_in_new_loop, input_str)
                    return future.result()
            except RuntimeError:
                # No event loop running, safe to create one
                return asyncio.run(self.coroutine(input_str))
        except Exception as e:
            error_msg = f"Sync execution error for {self.tool_name}: {str(e)}"
            logger.error(error_msg)
            return json.dumps({"error": error_msg})
    
    def _run_in_new_loop(self, input_str: str) -> str:
        """Run coroutine in a new event loop (for thread execution)"""
        return asyncio.run(self.coroutine(input_str))
    
    async def coroutine(self, input_str: str) -> str:
        """Async coroutine for MCP tool execution."""
        try:
            args = self._parse_arguments(input_str)

            logger.debug(f"Calling MCP tool {self.tool_name} with args={args}")
            result = await self.mcp_client.call_tool(self.tool_name, args)
            
            return self._format_result(result)
                
        except ValueError as e:
            # Argument parsing errors
            error_msg = f"Invalid arguments for {self.tool_name}: {str(e)}"
            logger.warning(error_msg)
            return json.dumps({"error": error_msg})
        except Exception as e:
            # Other execution errors
            error_msg = f"Error executing {self.tool_name}: {str(e)}"
            logger.error(error_msg)
            return json.dumps({"error": error_msg})
    
    def _parse_arguments(self, input_str: str) -> Dict[str, Any]:
        """Parse input string into tool arguments using registered parsers"""
        raw = input_str.strip() if isinstance(input_str, str) else input_str
        parsed_json = self._maybe_json(raw) if isinstance(raw, str) and raw.startswith(("{", "[")) else None
        
        parser = ParseStrategy.get_parser(self.tool_name)
        
        try:
            return parser.parse(raw, parsed_json)
        except ValueError as e:
            # Add more context to parsing errors
            logger.debug(f"Parsing failed for {self.tool_name}: args={parsed_json}, input='{raw}'")
            raise ValueError(f"{str(e)}: args={parsed_json}, input='{raw}'")
    
    @staticmethod
    def _maybe_json(raw: str) -> Optional[Union[Dict, List]]:
        """Helper function to safely parse JSON."""
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return None
    
    @staticmethod
    def _format_result(result: Any) -> str:
        """Format the result from MCP tool execution"""
        if isinstance(result, (dict, list)):
            return json.dumps(result, indent=2, ensure_ascii=False)
        else:
            return str(result)
    
    @classmethod
    def from_fastmcp_tool(cls, mcp_client: Any, fastmcp_tool) -> 'MCPExecutor':
        """Create MCPExecutor from FastMCP tool object"""
        # Extract schema information from FastMCP tool
        input_schema = fastmcp_tool.inputSchema
        if input_schema and 'properties' in input_schema:
            required_params = input_schema.get('required', [])
            properties = input_schema['properties']
            optional_params = [param for param in properties.keys() if param not in required_params]
            param_types = {param: props.get('type', 'string') for param, props in properties.items()}
            
            tool_schema = ToolSchema(
                name=fastmcp_tool.name,
                required_params=required_params,
                optional_params=optional_params,
                param_types=param_types
            )
        else:
            tool_schema = None
        
        return cls(mcp_client, fastmcp_tool.name, tool_schema)


def create_executors_from_fastmcp_tools(mcp_client: Any, fastmcp_tools: List) -> List[MCPExecutor]:
	"""Create MCPExecutor instances from FastMCP tools list"""
	return [MCPExecutor.from_fastmcp_tool(mcp_client, tool) for tool in fastmcp_tools]

