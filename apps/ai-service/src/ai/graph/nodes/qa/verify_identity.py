
from typing import Any, Dict, Optional

from ...states.qa import QAState
from ...types.qa import IdentificationState
from ...services.qa import ResponseService
from ...types.qa import Nodes, Routes

from utils import Logger

logger = Logger(__name__)


class VerifyIdentityNode:
    def __init__(
        self, 
        response_service: ResponseService
    ) -> None:
        self.response_service = response_service

    def __call__(
        self, 
        state: QAState
    ) -> QAState:
        logger.info(f"[NODE] Verifying user input")

        collected: Dict[str, Any] = state.get("collected_info", {}) or {}
        logger.info(f"Verifying identity with fields={list(collected.keys())}")

        required = ("name", "phone", "dob")
        has_all = all(collected.get(f) for f in required)
        state["current_node"] = Nodes.VERIFY_IDENTITY

        if has_all:
            message = self.response_service.run(
                {
                    "action": "verification_success", 
                    "user_name": collected.get("name")
                }
            )
            state["user_verified"] = True
            state["user_info"] = dict(collected)
            state["route"] = Routes.VERIFIED
            state["messages"] = state.get("messages", []) + [message]
            
            return state

        missing = [f for f in required if not collected.get(f)]

        message = self.response_service.run(
            {
                "action": "missing_required_fields", 
                "missing_fields": missing
            }
        )

        next_step = missing[0] if missing else "name"
        state["route"] = Routes.RETRY
        state["verification_step"] = next_step
        state["messages"] = state.get("messages", []) + [message]

        return state
