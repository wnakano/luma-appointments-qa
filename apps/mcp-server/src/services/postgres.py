import json
from typing import Any, Dict, List, Optional
import asyncpg
import os

from .base import ServiceModule
from utils import Logger

logger = Logger(__name__)



class DatabaseService(ServiceModule):
    """Database service module for PostgreSQL operations"""
    
    def __init__(self):
        self.db_pool: Optional[asyncpg.Pool] = None
        self._tools: List[Dict[str, Any]] = []
    
    async def initialize(self) -> None:
        """Initialize PostgreSQL connection pool"""
        try:
            database_url = os.getenv("DATABASE_URL")
            self.db_pool = await asyncpg.create_pool(
                database_url,
                min_size=1,
                max_size=10,
                command_timeout=30
            )
            logger.info("Database service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database service: {e}")
            raise
    
    async def cleanup(self) -> None:
        """Close database connection pool"""
        if self.db_pool:
            await self.db_pool.close()
            logger.info("Database service cleaned up")
    
    def register_tools(self, app) -> None:
        """Register database tools with FastMCP app"""
        
        @app.tool()
        async def db_query(query: str, params: List[Any] = None) -> str:
            """Execute a SELECT query against the database
            
            Args:
                query: SQL SELECT query to execute
                params: Query parameters for prepared statements
            """
            return await self._handle_db_query({"query": query, "params": params or []})
        
        @app.tool()
        async def db_write(query: str, params: List[Any] = None) -> str:
            """Execute INSERT, UPDATE, or DELETE operations
            
            Args:
                query: SQL write query (INSERT, UPDATE, DELETE)
                params: Query parameters for prepared statements
            """
            return await self._handle_db_write({"query": query, "params": params or []})
        
        @app.tool()
        async def db_transaction(queries: List[Dict[str, Any]]) -> str:
            """Execute multiple queries within a transaction
            
            Args:
                queries: Array of query objects with 'query' and optional 'params' keys
            """
            return await self._handle_db_transaction({"queries": queries})
        
        @app.tool()
        async def db_schema(table_name: str = None) -> str:
            """Get database schema information
            
            Args:
                table_name: Specific table name (optional)
            """
            return await self._handle_db_schema({"table_name": table_name})

        if not self._tools:
            self._tools.extend([
                {
                    "name": "db_query", 
                    "description": (db_query.__doc__ or "").strip().splitlines()[0] if db_query.__doc__ else "Execute a SELECT query",
                    "parameters": {
                        "query": {
                            "type": "string", 
                            "required": True
                        },
                        "params": {
                            "type": "array", 
                            "required": False
                        }
                }
                },
                {
                    "name": "db_write", 
                    "description": (db_write.__doc__ or "").strip().splitlines()[0] if db_write.__doc__ else "Execute write (INSERT/UPDATE/DELETE)",
                    "parameters": {
                        "query": {
                            "type": "string", 
                            "required": True
                        },
                        "params": {
                            "type": "array", 
                            "required": False
                        }
                    }
                },
                {
                    "name": "db_transaction", 
                    "description": (db_transaction.__doc__ or "").strip().splitlines()[0] if db_transaction.__doc__ else "Execute queries in a transaction",
                    "parameters": {
                        "queries": {
                            "type": "array", 
                            "required": True
                        }
                    }
                },
                {
                    "name": "db_schema", 
                    "description": (db_schema.__doc__ or "").strip().splitlines()[0] if db_schema.__doc__ else "Get database schema info",
                    "parameters": {
                        "table_name": {
                            "type": "string", 
                            "required": False
                        }
                    }
                },
            ])

    # Optional discovery hook used by server.list_tools
    def list_tools(self) -> List[Dict[str, Any]]:  # type: ignore[override]
        return self._tools
    
    async def _handle_db_query(self, arguments: Dict[str, Any]) -> str:
        """Handle database query operations"""
        query = arguments.get("query", "")
        params = arguments.get("params", [])
        
        if not query.strip().upper().startswith("SELECT"):
            return json.dumps({"error": "Only SELECT queries are allowed"}, indent=2)
        
        async with self.db_pool.acquire() as connection:
            try:
                if params:
                    rows = await connection.fetch(query, *params)
                else:
                    rows = await connection.fetch(query)
                
                result = [dict(row) for row in rows]
                
                return json.dumps({
                    "status": "success",
                    "rows_returned": len(result),
                    "data": result
                }, indent=2, default=str)
            except Exception as e:
                return json.dumps({"error": f"Query error: {str(e)}"}, indent=2)
    
    async def _handle_db_write(self, arguments: Dict[str, Any]) -> str:
        """Handle database write operations"""
        query = arguments.get("query", "")
        params = arguments.get("params", [])
        
        # Validate it's a write operation
        query_upper = query.strip().upper()
        if not any(query_upper.startswith(op) for op in ["INSERT", "UPDATE", "DELETE"]):
            return json.dumps({"error": "Only INSERT, UPDATE, DELETE queries are allowed"}, indent=2)
        
        async with self.db_pool.acquire() as connection:
            try:
                if params:
                    result = await connection.execute(query, *params)
                else:
                    result = await connection.execute(query)
                
                return json.dumps({
                    "status": "success",
                    "message": f"Query executed successfully: {result}"
                }, indent=2)
            except Exception as e:
                return json.dumps({"error": f"Write error: {str(e)}"}, indent=2)
    
    async def _handle_db_transaction(self, arguments: Dict[str, Any]) -> str:
        """Handle database transaction operations"""
        queries = arguments.get("queries", [])
        
        if not queries:
            return json.dumps({"error": "No queries provided"}, indent=2)
        
        async with self.db_pool.acquire() as connection:
            async with connection.transaction():
                try:
                    results = []
                    for query_info in queries:
                        query = query_info.get("query", "")
                        params = query_info.get("params", [])
                        
                        if params:
                            result = await connection.execute(query, *params)
                        else:
                            result = await connection.execute(query)
                        
                        results.append(str(result))
                    
                    return json.dumps({
                        "status": "success",
                        "message": "Transaction completed successfully",
                        "results": results
                    }, indent=2)
                except Exception as e:
                    return json.dumps({"error": f"Transaction error: {str(e)}"}, indent=2)
    
    async def _handle_db_schema(self, arguments: Dict[str, Any]) -> str:
        """Handle database schema information requests"""
        table_name = arguments.get("table_name")
        
        async with self.db_pool.acquire() as connection:
            try:
                if table_name:
                    # Get schema for specific table
                    query = """
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_name = $1
                    ORDER BY ordinal_position;
                    """
                    rows = await connection.fetch(query, table_name)
                else:
                    # Get all tables
                    query = """
                    SELECT table_name, table_type
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    ORDER BY table_name;
                    """
                    rows = await connection.fetch(query)
                
                result = [dict(row) for row in rows]
                
                return json.dumps({
                    "status": "success",
                    "schema_info": result
                }, indent=2, default=str)
            except Exception as e:
                return json.dumps({"error": f"Schema error: {str(e)}"}, indent=2)
