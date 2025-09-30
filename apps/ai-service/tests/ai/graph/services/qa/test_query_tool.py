"""Tests for QueryToolService (MCP-based database queries)."""
import pytest
from unittest.mock import AsyncMock, patch

from ..conftest import DEFAULT_MODEL, LOW_TEMPERATURE


@pytest.mark.unit
@pytest.mark.asyncio
class TestQueryToolService:
    """Test cases for QueryToolService (MCP-based database queries)."""
    
    async def test_query_tool_service_initialization(self, mock_openai_llm):
        """Test that QueryToolService initializes with low temperature for consistency."""
        from ai.graph.services.qa.query_tool import QueryToolService
        
        service = QueryToolService(model=DEFAULT_MODEL, temp=LOW_TEMPERATURE)
        
        assert service is not None
        assert hasattr(service, 'llm')
        assert hasattr(service, 'prompt_builder')
    
    @patch("ai.graph.services.qa.query_tool.MCPClientManager")
    async def test_execute_database_query(
        self, 
        mock_mcp_manager,
        sample_user_info
    ):
        """Test executing a database query through MCP client to find a user."""
        from ai.graph.services.qa.query_tool import QueryToolService
        from ai.graph.models.qa import ExtractedUserInfo
        
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.call_tool = AsyncMock(return_value={
            "results": [{"id": 1, "name": sample_user_info["name"]}]
        })
        mock_mcp_manager.return_value = mock_client
        
        with patch("ai.graph.services.llm.ChatOpenAI"):
            service = QueryToolService(model=DEFAULT_MODEL, temp=LOW_TEMPERATURE)
            
            user_info = ExtractedUserInfo(
                name=sample_user_info["name"],
                phone=sample_user_info["phone"],
                dob=sample_user_info["dob"]
            )
            
            result = await service.find_user(user_info)
            
            assert result is not None

