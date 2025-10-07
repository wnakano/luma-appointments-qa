
import os
from fastapi import APIRouter
from typing import (
	Any,
	List,
	Dict,
    Optional,
	Union
)
from copy import deepcopy
from pathlib import Path
from pydantic import ValidationError
from ai.graph.conversational_qa import QAGraph
from routers.models import (
    QAPayload, 
    QAResponse
)
from utils import (
	Logger,
	TimeHandler,

)
# from exceptions.custom import (
# 	ConfigError, 
#     DownloadError, 
#     OCRError, 
#     ParseError, 
#     MongoDBError,
#     UnknownError
# )

logger = Logger(__name__)


class ChatbotService:
    def __init__(self) -> None:
        self.qa_graph = QAGraph()
    
    async def run(
        self, 
        params: QAPayload
    ) -> QAResponse:
        start = TimeHandler.get_time()

        state = await self.qa_graph(
            user_message=params.user_message,
            request_id=params.request_id,
            session_id=params.session_id
        )

        end = TimeHandler.get_time()

        messages = state.get('messages', [])
        if messages:
            last_message = messages[-1]
            system_answer = last_message['system_message']
        else:
            system_answer = "Error in the QA"

        logger.info(f"[Answers] message = {messages}")
        return QAResponse(
            request_id=params.request_id,
            user_id=params.user_id,
            system_answer=system_answer,
            timestamp=TimeHandler.get_timestamp(tz="UTC"),
            elapsed_time=round(end - start, 4),
        )
