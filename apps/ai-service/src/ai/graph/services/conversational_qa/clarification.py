from typing import List, Optional, Dict

from ...models.conversational_qa import (
    VerificationInfoModel,
    AppointmentInfoModel
)
from ...prompts.templates.conversational_qa import ConversationalQAMessages
from utils import Logger

logger = Logger(__name__)


class ClarificationService:
    USER_FIELDS = ["full_name", "phone_number", "date_of_birth"]
    APPOINTMENT_FIELDS = ["doctor_full_name", "clinic_name", "appointment_date", "specialty"]
    FIELD_LABELS = {
        "full_name": "full name",
        "phone_number": "phone number",
        "date_of_birth": "date of birth",
        "doctor_full_name": "doctor's name",
        "clinic_name": "clinic name",
        "appointment_date": "appointment date",
        "specialty": "doctor's specialty"
    }
    
    def user_run(
        self,
        verification_info: Optional[VerificationInfoModel],
    ) -> str:
        try:
            logger.info("[SERVICE] ClarificationService.user_run")
            
            missing_fields = self._identify_missing_fields(
                verification_info, 
                self.USER_FIELDS
            )
            
            logger.info(f" ... Missing user fields: {missing_fields}")
            
            base_prompt = ConversationalQAMessages.base_clarification_user_system
            clarification_prompt = self._generate_clarification_prompt(
                base_prompt,
                missing_fields
            )
            
            return clarification_prompt
            
        except Exception as e:
            logger.error(f"[SERVICE] ClarificationService.user_run ERROR: {e}", exc_info=True)
            return self._get_fallback_prompt("user")
    
    def appointment_run(
        self,
        appointment_info: Optional[AppointmentInfoModel],
    ) -> str:
        try:
            logger.info("[SERVICE] ClarificationService.appointment_run")
            
            missing_fields = self._identify_missing_fields(
                appointment_info, 
                self.APPOINTMENT_FIELDS
            )
            
            logger.info(f" ... Missing appointment fields: {missing_fields}")
            
            base_prompt = ConversationalQAMessages.base_clarification_appointment_system
            clarification_prompt = self._generate_clarification_prompt(
                base_prompt,
                missing_fields
            )
            
            return clarification_prompt
            
        except Exception as e:
            logger.error(
                f"[SERVICE] ClarificationService.appointment_run ERROR: {e}", 
                exc_info=True
            )
            return self._get_fallback_prompt("appointment")
    
    def appointment_wait(
        self,
        appointment_info: Optional[AppointmentInfoModel] = None,
    ) -> str:
        try:
            logger.info("[SERVICE] ClarificationService.appointment_wait")
            
            system_prompt = ConversationalQAMessages.base_clarification_appointment_wait_system
            
            return system_prompt
            
        except Exception as e:
            logger.error(
                f"[SERVICE] ClarificationService.appointment_wait ERROR: {e}", 
                exc_info=True
            )
            return "Please provide more details about your appointment."
    
    def _identify_missing_fields(
        self,
        info_model: Optional[object],
        required_fields: List[str]
    ) -> List[str]:

        if not info_model:
            return required_fields.copy()
        
        missing_fields = []
        for field in required_fields:
            value = getattr(info_model, field, None)
            if not value or (isinstance(value, str) and not value.strip()):
                missing_fields.append(field)
        
        return missing_fields
    
    def _generate_clarification_prompt(
        self,
        base_prompt: str,
        missing_fields: List[str]
    ) -> str:
        if not missing_fields:
            logger.warning("No missing fields, but clarification was requested")
            return base_prompt + "the required information."
        
        missing_labels = [
            self.FIELD_LABELS.get(field, field.replace("_", " "))
            for field in missing_fields
        ]
        
        missing_text = self._format_list_with_grammar(missing_labels)
        
        return base_prompt + missing_text
    
    def _format_list_with_grammar(self, items: List[str]) -> str:

        if not items:
            return "the information"
        
        if len(items) == 1:
            return items[0]
        
        if len(items) == 2:
            return f"{items[0]} and {items[1]}"
        
        return ", ".join(items[:-1]) + f", and {items[-1]}"
    
    def _get_fallback_prompt(self, info_type: str) -> str:
        logger.warning(f"Returning fallback clarification prompt for {info_type}")
        
        if info_type == "user":
            return (
                ConversationalQAMessages.base_clarification_user_system +
                "your information."
            )
        else:
            return (
                ConversationalQAMessages.base_clarification_appointment_system +
                "the appointment details."
            )