from langchain.prompts import PromptTemplate 
from typing import Dict, List, Optional, Any

from ...models.conversational_qa import (
    VerificationInfoModel, 
    AppointmentInfoModel,
    ClarificationPromptModel
)
from ...prompts.templates.conversational_qa import ConversationalQAMessages
from ...states.conversational_qa import QAState, StateKeys
from ..llm import LLMService

from utils import Logger

logger = Logger(__name__)


class ClarificationService(LLMService):
    FIELD_LABELS = {
        "full_name": "full name",
        "phone_number": "phone number",
        "date_of_birth": "date of birth",
        "doctor_full_name": "doctor's name",
        "clinic_name": "clinic name",
        "appointment_date": "appointment date",
        "specialty": "doctor's specialty"
    }
    
    def __init__(
        self,
        model: str = "gpt-4o-mini",
        temp: float = 0.3
    ):

        super().__init__(model=model, temp=temp)
    
    def user_run(
        self,
        verification_info: Optional[VerificationInfoModel] = None,
        diagnostic_info: Optional[Dict] = None,
        conversation_context: Optional[str] = None
    ) -> str:
        """ Generate clarification prompt for user verification using LLM. """
        try:
            logger.info("[SERVICE] ClarificationService.user_run")
            
            context = self._build_user_context(
                verification_info,
                diagnostic_info
            )
            
            clarification = self._generate_user_clarification(
                context,
                conversation_context
            )
            
            logger.info(f" ... Generated clarification ({len(clarification)} chars)")
            return clarification
            
        except Exception as e:
            logger.error(f"[SERVICE] ClarificationService.user_run ERROR: {e}", exc_info=True)
            return self._get_fallback_user_prompt(verification_info, diagnostic_info)
    
    def appointment_run(
        self,
        appointment_info: Optional[AppointmentInfoModel] = None,
        diagnostic_info: Optional[Dict] = None,
        conversation_context: Optional[str] = None
    ) -> str:
        """ Generate clarification prompt for appointment information using LLM. """
        try:
            logger.info("[SERVICE] ClarificationService.appointment_run")
            
            context = self._build_appointment_context(
                appointment_info,
                diagnostic_info
            )
            logger.info(f"context = {context}")
            logger.info(f"conversation_context = {conversation_context}")
            
            clarification = self._generate_appointment_clarification(
                context,
                conversation_context
            )
            logger.info(f"clarification = {clarification}")
            
            logger.info(f" ... Generated clarification ({len(clarification)} chars)")
            return clarification
            
        except Exception as e:
            logger.error(
                f"[SERVICE] ClarificationService.appointment_run ERROR: {e}",
                exc_info=True
            )
            return self._get_fallback_appointment_prompt(appointment_info, diagnostic_info)
    
    def appointment_wait(
        self,
        appointment_info: Optional[AppointmentInfoModel] = None
    ) -> str:
        """ Generate prompt for waiting on appointment details. """
        logger.info("[SERVICE] ClarificationService.appointment_wait")
        return ConversationalQAMessages.base_clarification_appointment_wait_system

    def _build_user_context(
        self,
        verification_info: Optional[VerificationInfoModel],
        diagnostic_info: Optional[Dict]
    ) -> Dict[str, Any]:
        """ Build context dictionary for user verification clarification. """
        context = {
            "has_verification_info": verification_info is not None,
            "has_diagnostics": diagnostic_info is not None
        }
        
        if verification_info:
            context["current_info"] = {
                "full_name": verification_info.full_name or "not provided",
                "phone_number": verification_info.phone_number or "not provided",
                "date_of_birth": verification_info.date_of_birth or "not provided"
            }
        else:
            context["current_info"] = {
                "full_name": "not provided",
                "phone_number": "not provided",
                "date_of_birth": "not provided"
            }
        
        if diagnostic_info:
            context["diagnostic"] = {
                "reason": diagnostic_info.get("reason", "unknown"),
                "likely_incorrect": diagnostic_info.get("likely_incorrect", []),
                "possibly_correct": diagnostic_info.get("possibly_correct", []),
                "missing_fields": diagnostic_info.get("missing_fields", []),
                "message": diagnostic_info.get("message", "")
            }
        else:
            context["diagnostic"] = None
        
        return context
    
    def _build_appointment_context(
        self,
        appointment_info: Optional[AppointmentInfoModel],
        diagnostic_info: Optional[Dict]
    ) -> Dict[str, Any]:
        """
        Build context dictionary for appointment clarification. """
        logger.info(f" ... Building appointment context: {diagnostic_info}")
        context = {
            "has_appointment_info": appointment_info is not None,
            "has_diagnostics": diagnostic_info is not None
        }
        
        if appointment_info:
            context["current_info"] = {
                "doctor_name": appointment_info.doctor_full_name or "not provided",
                "clinic_name": appointment_info.clinic_name or "not provided",
                "appointment_date": appointment_info.appointment_date or "not provided",
                "specialty": appointment_info.specialty or "not provided"
            }
        else:
            context["current_info"] = {
                "doctor_name": "not provided",
                "clinic_name": "not provided",
                "appointment_date": "not provided",
                "specialty": "not provided"
            }
        
        if diagnostic_info:
            context["diagnostic"] = {
                "missing_fields": diagnostic_info.get("missing_fields", []),
                "likely_incorrect": diagnostic_info.get("likely_incorrect", []),
                "possibly_correct": diagnostic_info.get("possibly_correct", []),
                "existing_appointments_summary": diagnostic_info.get("existing_appointments_summary", ""),
                "message": diagnostic_info.get("message", "")
            }
        else:
            context["diagnostic"] = None
        
        return context
    
    def _generate_user_clarification(
        self,
        context: Dict[str, Any],
        conversation_context: Optional[str] = None
    ) -> str:
        """Generate user clarification prompt using LLM. """
        system_prompt = ConversationalQAMessages.clarification_user_system
        human_prompt = ConversationalQAMessages.clarification_user_prompt

        diagnostic_summary = self._format_user_diagnostic_for_prompt(
            context.get("diagnostic")
        )
        
        current_info = context.get("current_info", {})
        
        template = self.build_prompt_template(
            system_prompt=system_prompt,
            human_prompt=human_prompt,
            system_input_variables=["context"],
            human_input_variables=[
                "full_name", "phone_number", 
                "date_of_birth", "diagnostic_summary"
            ]
        )
        
        chain = self.build_structured_chain(
            template=template,
            schema=ClarificationPromptModel
        )
        
        result = chain.invoke({
            "context": str(context),
            "full_name": current_info.get("full_name", "not provided"),
            "phone_number": current_info.get("phone_number", "not provided"),
            "date_of_birth": current_info.get("date_of_birth", "not provided"),
            "diagnostic_summary": diagnostic_summary
        })
        
        return result.clarification_prompt
    
    def _generate_appointment_clarification(
        self,
        context: Dict[str, Any],
        conversation_context: Optional[str] = None
    ) -> str:
        """ Generate appointment clarification prompt using LLM. """
        
        diagnostic_summary = self._format_appointment_diagnostic_for_prompt(
            context.get("diagnostic")
        )

        logger.info(f"... (_generate_appointment_clarification) diagnostic_summary = {diagnostic_summary}")

        system_prompt = ConversationalQAMessages.clarification_appointment_system
        human_prompt = ConversationalQAMessages.clarification_appointment_prompt
        
        current_info = context.get("current_info", {})
        
        template = self.build_prompt_template(
            system_prompt=system_prompt,
            human_prompt=human_prompt,
            system_input_variables=["context"],
            human_input_variables=[
                "doctor_name", "clinic_name", 
                "appointment_date", "specialty",
                "diagnostic_summary"
            ]
        )

        logger.info(f" ... Appointment clarification template: {template}")
        
        chain = self.build_structured_chain(
            template=template,
            schema=ClarificationPromptModel
        )
        
        result = chain.invoke({
            "context": str(context),
            "doctor_name": current_info.get("doctor_name", "not provided"),
            "clinic_name": current_info.get("clinic_name", "not provided"),
            "appointment_date": current_info.get("appointment_date", "not provided"),
            "specialty": current_info.get("specialty", "not provided"),
            "diagnostic_summary": diagnostic_summary
        })
        
        return result.clarification_prompt

    def _format_user_diagnostic_for_prompt(self, diagnostic: Optional[Dict]) -> str:
        """ Format diagnostic information into readable text for LLM prompt. """
        if not diagnostic:
            return "No specific diagnostic information available."
        
        parts = []
        
        # Reason
        reason = diagnostic.get("reason")
        if reason:
            reason_descriptions = {
                "no_info_provided": "User has not provided any information yet",
                "incomplete_info": "User has provided partial information",
                "user_not_found": "No user found with the provided information",
                "single_field_incorrect": "One field doesn't match our records",
                "multiple_fields_incorrect": "Multiple fields don't match our records",
                "no_complete_match": "Partial matches found but no complete match"
            }
            parts.append(f"Situation: {reason_descriptions.get(reason, reason)}")
        
        missing = diagnostic.get("missing_fields", [])
        if missing:
            friendly_names = [self.FIELD_LABELS.get(f, f) for f in missing]
            parts.append(f"Missing: {', '.join(friendly_names)}")
        
        incorrect = diagnostic.get("likely_incorrect", [])
        if incorrect:
            friendly_names = [self.FIELD_LABELS.get(f, f) for f in incorrect]
            parts.append(f"Likely incorrect: {', '.join(friendly_names)}")
        
        correct = diagnostic.get("possibly_correct", [])
        if correct:
            friendly_names = [self.FIELD_LABELS.get(f, f) for f in correct]
            parts.append(f"Possibly correct: {', '.join(friendly_names)}")
        
        message = diagnostic.get("message")
        if message:
            parts.append(f"Diagnostic message: {message}")
        
        return "\n".join(parts) if parts else "No diagnostic details available."
    
    def _format_appointment_diagnostic_for_prompt(self, diagnostic: Optional[Dict]) -> str:
        """ Format diagnostic information into readable text for LLM prompt. """
        if not diagnostic:
            return "No specific diagnostic information available."
        
        parts = []
        
        # Reason
        reason = diagnostic.get("reason")
        if reason:
            reason_descriptions = {
                "no_info_provided": "User has not provided any information yet",
                "incomplete_info": "User has provided partial information",
                "user_not_found": "No user found with the provided information",
                "single_field_incorrect": "One field doesn't match our records",
                "multiple_fields_incorrect": "Multiple fields don't match our records",
                "no_complete_match": "Partial matches found but no complete match",
                "no_appointments": "User has no scheduled appointments",
                "single_field_mismatch": "One field doesn't match the closest appointment",
                "partial_match": "Some fields match but not all",
                "no_matches": "No appointments match the provided information"
            }
            parts.append(f"Situation: {reason_descriptions.get(reason, reason)}")
        
        # Missing fields
        missing = diagnostic.get("missing_fields", [])
        if missing:
            friendly_names = [self.FIELD_LABELS.get(f, f) for f in missing]
            parts.append(f"Missing: {', '.join(friendly_names)}")
        
        # Incorrect fields
        incorrect = diagnostic.get("likely_incorrect", [])
        if incorrect:
            friendly_names = [self.FIELD_LABELS.get(f, f) for f in incorrect]
            parts.append(f"Likely incorrect: {', '.join(friendly_names)}")
        
        # Correct fields
        correct = diagnostic.get("possibly_correct", [])
        if correct:
            friendly_names = [self.FIELD_LABELS.get(f, f) for f in correct]
            parts.append(f"Possibly correct: {', '.join(friendly_names)}")
        
        # Closest match information (for appointments)
        closest_match = diagnostic.get("closest_match")
        if closest_match:
            parts.append("\nClosest matching appointment:")
            parts.append(f"  Doctor: {closest_match.get('doctor_name', 'N/A')}")
            parts.append(f"  Clinic: {closest_match.get('clinic_name', 'N/A')}")
            parts.append(f"  Date: {closest_match.get('appointment_date', 'N/A')}")
            parts.append(f"  Specialty: {closest_match.get('specialty', 'N/A')}")
        
        # Existing appointments summary (for appointments)
        existing_summary = diagnostic.get("existing_appointments_summary")
        if existing_summary:
            parts.append(f"\nUser's scheduled appointments:\n{existing_summary}")
        
        # Diagnostic message
        message = diagnostic.get("message")
        if message:
            parts.append(f"\nDiagnostic message: {message}")
        
        return "\n".join(parts) if parts else "No diagnostic details available."
    
    def _get_fallback_user_prompt(
        self,
        verification_info: Optional[VerificationInfoModel],
        diagnostic_info: Optional[Dict]
    ) -> str:
        """ Get fallback clarification prompt for user verification. """
        logger.warning("Using fallback user prompt")
        
        if diagnostic_info and diagnostic_info.get("message"):
            return diagnostic_info["message"]
        
        if not verification_info:
            return "Please provide your full name, phone number, and date of birth to verify your identity."
        
        missing = []
        if not verification_info.full_name:
            missing.append("full name")
        if not verification_info.phone_number:
            missing.append("phone number")
        if not verification_info.date_of_birth:
            missing.append("date of birth")
        
        if missing:
            return f"Please provide your {self._format_list_with_grammar(missing)}."
        
        return "We couldn't verify your identity. Please check your information and try again."
    
    def _get_fallback_appointment_prompt(
        self,
        appointment_info: Optional[AppointmentInfoModel],
        diagnostic_info: Optional[Dict]
    ) -> str:
        """ Get fallback clarification prompt for appointment."""
        logger.warning("Using fallback appointment prompt")
        
        if diagnostic_info and diagnostic_info.get("message"):
            return diagnostic_info["message"]
        
        if not appointment_info:
            return (
                "Please provide details about your appointment such as the doctor's name, "
                "clinic name, appointment date, or specialty."
            )
        
        missing = []
        if not appointment_info.doctor_full_name:
            missing.append("doctor's name")
        if not appointment_info.clinic_name:
            missing.append("clinic name")
        if not appointment_info.appointment_date:
            missing.append("appointment date")
        if not appointment_info.specialty:
            missing.append("specialty")
        
        if missing:
            return f"Please provide the {self._format_list_with_grammar(missing)} for your appointment."
        
        return "We need more information to identify your appointment."
    
    def _format_list_with_grammar(self, items: List[str]) -> str:
        """ Format a list of strings into a grammatically correct phrase."""
        if not items:
            return ""
        if len(items) == 1:
            return items[0]
        if len(items) == 2:
            return f"{items[0]} and {items[1]}"
        return ", ".join(items[:-1]) + f", and {items[-1]}"