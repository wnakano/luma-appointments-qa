from typing import Dict, Any
from fastapi import APIRouter, Depends, Request
from utils import TimeHandler

class HealthRouter:
    def __init__(self) -> None:
        self.router = APIRouter(prefix="/api/v1/health", tags=["meta"])
        self.router.add_api_route("/checker", self.health_check, methods=["GET"])

    async def health_check(
        self,
    ) -> Dict[str, Any]:
        return {
            "status": "RUNNING",
            "timestamp": TimeHandler.get_timestamp()
        }
