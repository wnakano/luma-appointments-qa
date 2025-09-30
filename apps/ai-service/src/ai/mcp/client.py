from typing import Any, Dict, List, Optional, Union
from fastmcp import Client

from .tools import MCPTool, MCPToolFactory
from utils import Logger

logger = Logger(__name__)


class MCPClientManager:
    """Centralized MCP client manager for handling MCP server interactions"""
    
    def __init__(self, server_url: str):
        self.server_url = server_url
        self._client: Optional[Client] = None
        self._tools_cache: Optional[List[Dict[str, Any]]] = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self._client = Client(self.server_url)
        await self._client.__aenter__()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self._client:
            await self._client.__aexit__(exc_type, exc_val, exc_tb)
            self._client = None
            self._tools_cache = None
    
    async def health_check(self) -> Dict[str, Any]:
        """Check MCP server health"""
        if not self._client:
            raise RuntimeError("MCP client not initialized")
        
        try:
            # Assuming your server has a health endpoint
            return await self._client.call_tool("health", {})
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            return {"status": "unknown", "error": str(e)}
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """Get available MCP tools"""
        if not self._client:
            raise RuntimeError("MCP client not initialized")
        
        if self._tools_cache is None:
            self._tools_cache = await self._client.list_tools()
        
        return self._tools_cache
    
    async def get_langchain_tools(self) -> List[MCPTool]:
        """Convert MCP tools to LangChain tools"""
        tools_list = await self.list_tools()
        langchain_tools = MCPToolFactory.create_tools_from_config(
            mcp_client=self._client,
            tools_list=tools_list
        )
        return langchain_tools

    async def get_langchain_tools(self) -> List[MCPTool]:
        """Convert MCP tools to LangChain tools"""
        tools_list = await self.list_tools()
        langchain_tools = MCPToolFactory.create_tools_from_config(
            mcp_client=self._client,
            tools_list=tools_list
        )
        return langchain_tools
        
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a specific MCP tool"""
        if not self._client:
            raise RuntimeError("MCP client not initialized")
        
        try:
            return await self._client.call_tool(tool_name, arguments)
        except Exception as e:
            logger.error(f"Error calling MCP tool {tool_name}: {e}")
            raise
    
    async def execute_db_query(self, query: str, params: Optional[List[Any]] = None) -> Dict[str, Any]:
        """Execute a database query via MCP"""
        return await self.call_tool("db_query", {
            "query": query,
            "params": params or []
        })
    
    async def execute_db_write(self, query: str, params: Optional[List[Any]] = None) -> Dict[str, Any]:
        """Execute a database write operation via MCP"""
        return await self.call_tool("db_write", {
            "query": query,
            "params": params or []
        })
    
    async def get_db_schema(self, table_name: Optional[str] = None) -> Dict[str, Any]:
        """Get database schema information via MCP"""
        return await self.call_tool("db_schema", {
            "table_name": table_name
        })
