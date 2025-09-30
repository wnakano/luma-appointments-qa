from fastapi import Depends, FastAPI, HTTPException, Request

from routers.health import HealthRouter
from routers.chatbot import ChatbotRouter
from utils import Logger

logger = Logger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(
        title="Lumahealth QA Appointments",
        version="1.0.0",
        description="QA API",
    )

    qa_router = ChatbotRouter()
    health_router = HealthRouter()
    
    app.include_router(qa_router.router)
    app.include_router(health_router.router)

    return app


app = create_app()