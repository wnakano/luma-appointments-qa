import json
import requests
import os
import time
import uuid
from typing import Dict, Any, Optional

from utils import Logger

logger = Logger(__name__)


class ChatbotAPIClient:
    def __init__(self):
        self.api_url = os.getenv("CHATBOT_API_URL")

        if not self.api_url:
            raise ValueError("CHATBOT_API_URL environment variable is required")

    
    def send_message(
        self, 
        request_id: str,
        user_id: str,
        session_id: str,
        message: str, 
        conversation_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        headers = {
            "Content-Type": "application/json"
        }
        
        payload = {
            "request_id": request_id,
            "user_id": user_id,
            "session_id": session_id,
            "user_message": message,
        }
        logger.info(f"payload = {payload}")
        # if conversation_context:
        #     payload["context"] = conversation_context
        
        try:
            start_time = time.time()
            response = requests.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=120
            )
            end_time = time.time()
            
            response.raise_for_status()
            
            result = response.json()
            result["latency_ms"] = int((end_time - start_time) * 1000)
            result["request_id"] = payload["request_id"]
            
            return result
            
        except requests.exceptions.RequestException as e:
            return {
                "error": str(e),
                "message": "Sorry, I'm having trouble connecting to the chatbot service. Please try again.",
                "request_id": payload["request_id"],
                "latency_ms": int((time.time() - start_time) * 1000) if 'start_time' in locals() else 0
            }

