import re
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List

from ..types.conversational_qa import (
    IntentType,
    ConfirmationIntent
)


class UserIntentModel(BaseModel):
    """Base model for user intent classification"""
    intent_type: IntentType = Field(
        description="The primary intent of the user's message"
    )
    confidence: float = Field(
        description="Confidence score between 0 and 1",
        ge=0.0,
        le=1.0
    )


class VerificationInfoModel(BaseModel):
    """Model for extracting user verification information"""
    full_name: Optional[str] = Field(
        None,
        description="User's full name if provided"
    )
    phone_number: Optional[str] = Field(
        None,
        description="Phone number in format like 555-0123 or (555) 012-3456"
    )
    date_of_birth: Optional[str] = Field(
        None,
        description="Date of birth in format like 'March 15, 1985' or '03/15/1985'"
    )

    @field_validator('full_name')
    @classmethod
    def format_full_name(cls, v: Optional[str]) -> Optional[str]:
        if not v or not isinstance(v, str):
            return v
        return v.title()
    
    @field_validator('phone_number')
    @classmethod
    def validate_phone_number(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        pattern = r'^\+\d{10,15}$'
        if not re.match(pattern, v):
            v = ""
        return v

    # @field_validator('date_of_birth')
    # @classmethod
    # def validate_date_of_birth(cls, v: Optional[datetime]) -> Optional[datetime]:
    #     if v is None:
    #         return v
        
    #     if v > datetime.now():
    #         return None
        
    #     if v.year < 1900:
    #         return None
        
    #     return v

class VerificationRecordModel(BaseModel):
    """Model for extracting user verification information"""
    user_id: Optional[str] = Field(
        None,
        description="User's ID"
    )
    full_name: Optional[str] = Field(
        None,
        description="User's full name if provided"
    )
    phone_number: Optional[str] = Field(
        None,
        description="Phone number in format like +<country_code><number> (e.g., +1234567890)"
    )
    date_of_birth: Optional[datetime] = Field(
        None,
        description="Date of birth in format YYYY-MM-DD (e.g., 1990-01-01)"
    )
    
    
class AppointmentInfoModel(BaseModel):
    """Model for referencing a specific appointment"""
    doctor_full_name: Optional[str] = Field(
        None, 
        description="Full name of the doctor for the appointment"
    )
    clinic_name: Optional[str] = Field(
        None, 
        description="Name of the clinic or medical facility where the appointment takes place"
    )
    appointment_date: Optional[str] = Field(
        None, 
        description="Date and time of the appointment (e.g., '2025-10-15' or '2025-10-15 14:30')"
    )
    specialty: Optional[str] = Field(
        None, 
        description="Medical specialty of the doctor (e.g., 'Cardiology', 'Dermatology', 'General Practice')"
    )

class AppointmentRecordModel(BaseModel):
    """Model for referencing a specific appointment"""
    appointment_id: Optional[str] = Field(
        None, 
        description=""
    )
    doctor_full_name: Optional[str] = Field(
        None, 
        description="Full name of the doctor for the appointment"
    )
    clinic_name: Optional[str] = Field(
        None, 
        description="Name of the clinic or medical facility where the appointment takes place"
    )
    appointment_date: Optional[str] = Field(
        None, 
        description="Date and time of the appointment (e.g., '2025-10-15' or '2025-10-15 14:30')"
    )
    specialty: Optional[str] = Field(
        None, 
        description="Medical specialty of the doctor (e.g., 'Cardiology', 'Dermatology', 'General Practice')"
    )

class AppointmentMatchModel(BaseModel):
    match_found: bool = Field(
        description="Whether a matching appointment was found based on the search criteria"
    )
    confidence: float = Field(
        description="Confidence score between 0 and 1",
        ge=0.0,
        le=1.0
    )
    matched_appointment_id: Optional[str] = Field(
        None,
        description="The ID of the best matching appointment, or null if no match found"
    )
    reasoning: str = Field(
        description="Explanation of why this appointment was selected or why no match was found"
    )


class ConversationIntentModel(BaseModel):
    """Complete intent classification with extracted entities"""
    
    user_intent: UserIntentModel
    verification_info: Optional[VerificationInfoModel] = None
    appointment_info: Optional[AppointmentInfoModel] = None
    raw_query: str = Field(description="The original user query")


class AppointmentConfirmationResponse(BaseModel):
    """
    Structured response for appointment confirmation classification.
    This model is used to bind LLM outputs for appointment confirmations.
    """
    intent: ConfirmationIntent = Field(
        ...,
        description="The patient's intent regarding the appointment change: confirm, reject, or unclear"
    )
    confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Confidence score of the classification (0.0 to 1.0)"
    )
    reasoning: Optional[str] = Field(
        None,
        description="Brief explanation of why this intent was classified"
    )
    extracted_concerns: Optional[str] = Field(
        None,
        description="Any concerns or conditions mentioned by the patient"
    )

    class Config:
        use_enum_values = True


class QAAnswerModel(BaseModel):
    qa_answer: str = Field(
        ...,
        description="Assistant answer based on user's question"
    )


class ClarificationPromptModel(BaseModel):
    clarification_prompt: str = Field(
        ...,
        description="Clarification prompt asking user for more details"
    )