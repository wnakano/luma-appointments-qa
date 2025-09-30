import asyncio
import concurrent.futures

from typing import Any, Dict, Optional

from ...states.qa import QAState
from ...types.qa import IdentificationState, Routes
from ...services.qa import ResponseService, QueryToolService
from ...models.qa import UserValidationResult
from ...types.qa import Nodes, Routes

from utils import Logger

logger = Logger(__name__)


class AsyncQueryIdentityNode:
    def __init__(
        self, 
        query_tool_service: QueryToolService,
        response_service: ResponseService
    ) -> None:
        self.query_tool_service = query_tool_service
        self.response_service = response_service

    async def __call__(
        self, 
        state: QAState
    ) -> QAState:
        logger.info(f"[NODE] Querying user identity")
        collected: Dict[str, Any] = state.get("collected_info") 
        user_info = UserValidationResult(
            patient_id="",
            is_valid=False,
            full_name=collected.get("name"),
            date_of_birth=collected.get("dob"),
            phone=collected.get("phone")
        )
        state["current_node"] = Nodes.QUERY_IDENTITY
        try:
            result = await self.query_tool_service.find_user(
                user_info=user_info
            )

            if result.is_valid and result.patient_id:
                state["user_verified"] = True
                state["user_info_db"] = result.model_dump()
                state["route"] = Routes.MATCH                
            else:
                state["user_verified"] = True
                state["route"] = Routes.NOT_MATCH
                
            return state

        except Exception as e:
            state["user_verified"] = False
            state["user_info_db"] = ""
            state["route"] = Routes.NOT_MATCH

        return state

class QueryIdentityNode(AsyncQueryIdentityNode):
    def __init__(
        self, 
        query_tool_service: QueryToolService,
        response_service: ResponseService
    ) -> None:
        super().__init__(query_tool_service, response_service)
    
    def __call__(self, state: QAState) -> QAState:
        """Synchronous call that runs the async method"""
        try:
            # Run the async method in the current event loop if available
            loop = asyncio.get_event_loop()
            if loop.is_running():
 
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, super().__call__(state))
                    result = future.result(timeout=300) 
                    return result
            else:
                return asyncio.run(super().__call__(state))
                
        except Exception as e:
            logger.error(f"Error in sync wrapper: {e}")
            return self._handle_verification_failure(
                state,
                f"System error: {str(e)}",
                "system_error"
            )