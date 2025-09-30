
from datetime import datetime, date
from pydantic import BaseModel, Field, field_validator
from typing import (
    Any, Dict, Literal, 
    List, Optional, Union
)


class ExtractedInfo(BaseModel):
	"""Model for extracted user information"""
	has_relevant_info: bool = Field(description="Whether the message contains relevant user information")
	extracted_value: Optional[str] = Field(description="The extracted value if found")
	confidence: float = Field(description="Confidence score 0-1")
	requires_clarification: bool = Field(description="Whether clarification is needed")
	clarification_message: Optional[str] = Field(description="Message to ask for clarification")

class ValidationResult(BaseModel):
	"""Model for validation results"""
	is_valid: bool = Field(description="Whether the input is valid")
	cleaned_value: Optional[str] = Field(description="Cleaned/formatted version of the input")
	error_message: Optional[str] = Field(description="Error message if validation failed")
	suggestions: Optional[List[str]] = Field(description="Suggestions for correction")

class UserIntent(BaseModel):
	"""Model for understanding user intent"""
	is_providing_info: bool = Field(description="Whether user is providing requested information")
	is_asking_question: bool = Field(description="Whether user is asking a question")
	is_correction: bool = Field(description="Whether user is correcting previous information")
	wants_to_skip: bool = Field(description="Whether user wants to skip verification")


class ExtractedUserInfo(BaseModel):
	"""Model for extracted user information"""
	user_id: Optional[str] = Field(
		default=None,
		description="User ID if available from context"
	)
	full_name: Optional[str] = Field(
		default=None,
		description="User's full name as extracted from the message"
	)
	
	birthday: Optional[date] = Field(
		default=None,
		description="User's birthday in YYYY-MM-DD format"
	)
	
	phone_number: Optional[str] = Field(
		default=None,
		description="User's phone number in standardized format"
	)
	
	# Optional additional fields that might be useful
	email: Optional[str] = Field(
		default=None,
		description="User's email address if mentioned"
	)
	
	confidence_score: float = Field(
		default=0.0,
		ge=0.0,
		le=1.0,
		description="Overall confidence score for the extraction (0-1)"
	)


class UserValidationResult(BaseModel):
	"""
	Result of user validation/search operations containing user data and metadata
	"""
	is_valid: bool = Field(
		default=False,
		description="Whether a valid user was found"
	)
	# Core validation status
	patient_id: str = Field(
		default=None,
		description="Unique identifier of the user if found"
	)
	
	full_name: str = Field(
		default=None,
		description="User's full name if found"
	)
	
	phone: Optional[str] = Field(
		default=None,
		description="User's phone number if found"
	)
	
	# User data and metadata
	date_of_birth: Optional[date] = Field(
		default=None,
		description="User's birthday in YYYY-MM-DD format"
	)

	@field_validator("date_of_birth", mode="before")
	def parse_dob(cls, v):
		if v is None:
			return v
		if isinstance(v, date):
			return v
		return datetime.strptime(v, "%Y-%m-%d").date()
	