from pydantic import BaseModel, field_validator
from typing import (
	Dict,
	Optional
)


class QAPayload(BaseModel):
	request_id: Optional[str]
	user_id: Optional[str]
	user_message: str
	session_id: str


class QAResponse(BaseModel):
	request_id: Optional[str]
	user_id: Optional[str]
	system_answer: str
	

class ErrorResponse(BaseModel):
	error: str

