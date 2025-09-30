from fastapi import Request, Depends, HTTPException
from pathlib import Path
from typing import (
	Dict, 
	List,
	Union
)   

from routers.base import BaseRouter
from routers.models import (
	QAPayload, 
	QAResponse,
	ErrorResponse
)
from routers.status import APIStatus
from services.chatbot import ChatbotService

from utils import Logger

logger = Logger(__name__)


def get_chatbot_service() -> "ChatbotService":
    return ChatbotService()


class ChatbotRouter(BaseRouter):
	def __init__(self):
		super().__init__(prefix="/api/v1/chatbot", tags=["data"])
		self.temp_dir = Path("temp")
		self.temp_dir.mkdir(parents=True, exist_ok=True)

	def register_routes(self) -> None:
		self.router.add_api_route(
			"/question",
			self.question,
			methods=["POST"],
			response_model=Union[QAResponse, ErrorResponse],
			status_code=200,
			responses={
				400: {"model": ErrorResponse, "description": "Bad request"},
				422: {"model": ErrorResponse, "description": "Validation error"},
				500: {"model": ErrorResponse, "description": "Internal server error"},
				502: {"model": ErrorResponse, "description": "QA error"},
			},
		)

	async def question(
		self, 
		payload: QAPayload,
		chatbot_service: ChatbotService = Depends(get_chatbot_service)
		) -> Union[QAResponse, ErrorResponse]:
		return await chatbot_service.run(params=payload)
	