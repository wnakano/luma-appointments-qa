from pydantic import BaseModel, field_validator
from typing import (
	Dict,
	Optional
)


class QAPayload(BaseModel):
	request_id: Optional[str] = None
	user_id: Optional[str] = None
	user_message: str
	session_id: str


class QAResponse(BaseModel):
	request_id: Optional[str] = None
	user_id: Optional[str] = None
	system_answer: str
	timestamp: Optional[str] = None
	elapsed_time: Optional[float] = None
	

class ErrorResponse(BaseModel):
	error: str

