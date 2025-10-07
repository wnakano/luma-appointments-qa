from langchain.prompts import PromptTemplate 
from textwrap import dedent
from typing import Any, Dict, List, Optional, Tuple

from ...states.conversational_qa import QAState
from ...types.conversational_qa import (
    Routes, 
    Nodes,
    IntentType
)
from ...prompts.templates.conversational_qa import ConversationalQAMessages
from ...models.conversational_qa import AppointmentInfoModel, AppointmentMatchModel
from ..llm import LLMService
from .query_orm import QueryORMService
from utils import Logger

logger = Logger(__name__)


class AppointmentMatchService(LLMService):
    def __init__(
        self,
        query_orm_service: QueryORMService,
        model: str = "gpt-4o-mini",
        temp: float = 0.0,
    ) -> None:
        super().__init__(model=model, temp=temp)
        self.query_orm_service = query_orm_service
    
    def run(
        self, 
        appointments: List[Dict[str, Any]],
        appointment_info: AppointmentInfoModel
    ) -> AppointmentMatchModel:
        try:
            logger.info("[SERVICE] AppointmentMatchService")
            
            self._validate_inputs(appointments, appointment_info)
            
            logger.info(f" ... Matching against {len(appointments)} appointment(s)")
            
            direct_matches = self._find_direct_matches(appointments, appointment_info)
            
            if len(direct_matches) == 1:
                matched_appt = direct_matches[0]
                logger.info(
                    f" ... Direct match found: Appointment ID {matched_appt['id']}"
                )
                return AppointmentMatchModel(
                    match_found=True,
                    confidence=1.0,
                    matched_appointment_id=str(matched_appt['id']),
                    reasoning="Direct match found based on provided criteria"
                )
            
            elif len(direct_matches) == 0:
                logger.info(" ... No direct matches found, using LLM for intelligent matching")
            else:
                logger.info(
                    f" ... {len(direct_matches)} direct matches found, "
                    "using LLM to disambiguate"
                )
            
            result = self._match_with_llm(appointments, appointment_info)
            
            return result
            
        except Exception as e:
            logger.error(f"[SERVICE] AppointmentMatchService ERROR: {e}", exc_info=True)
            return self._get_fallback_response()
    
    def _find_direct_matches(
        self,
        appointments: List[Dict[str, Any]],
        appointment_info: AppointmentInfoModel
    ) -> List[Dict[str, Any]]:
        matches = []
        
        for appt in appointments:
            if self._is_direct_match(appt, appointment_info):
                matches.append(appt)
        
        return matches
    
    def _is_direct_match(
        self,
        appointment: Dict[str, Any],
        appointment_info: AppointmentInfoModel
    ) -> bool:
        if appointment_info.doctor_full_name:
            appt_doctor = appointment.get('provider', {}).get('full_name', '')
            if not self._strings_match(appointment_info.doctor_full_name, appt_doctor):
                return False
        
        if appointment_info.clinic_name:
            appt_clinic = appointment.get('clinic', {}).get('name', '')
            if not self._strings_match(appointment_info.clinic_name, appt_clinic):
                return False
        
        if appointment_info.specialty:
            appt_specialty = appointment.get('provider', {}).get('specialty', '')
            if not self._strings_match(appointment_info.specialty, appt_specialty):
                return False
        
        if appointment_info.appointment_date:
            appt_date = appointment.get('starts_at', '')
            if not self._dates_match(appointment_info.appointment_date, appt_date):
                return False
        
        return True
    
    def _strings_match(self, str1: str, str2: str) -> bool:
        if not str1 or not str2:
            return False
        
        normalized1 = str1.lower().strip()
        normalized2 = str2.lower().strip()
        
        return normalized1 in normalized2 or normalized2 in normalized1
    
    def _dates_match(self, date1: str, date2: str) -> bool:
        if not date1 or not date2:
            return False
        
        date1_norm = date1.lower().strip()
        date2_norm = date2.lower().strip()
        
        return date1_norm in date2_norm or date2_norm in date1_norm
    
    def _match_with_llm(
        self,
        appointments: List[Dict[str, Any]],
        appointment_info: AppointmentInfoModel
    ) -> AppointmentMatchModel:
        doctor_full_name = appointment_info.doctor_full_name or ""
        clinic_name = appointment_info.clinic_name or ""
        appointment_date = appointment_info.appointment_date or ""
        specialty = appointment_info.specialty or ""
        
        criteria_text = self._format_criteria(appointment_info)
        appointments_text = self._format_appointments(appointments)
        
        template = self._build_prompt_template()
        chain = self.build_structured_chain(
            template=template,
            schema=AppointmentMatchModel
        )
        
        result: AppointmentMatchModel = chain.invoke({
            "criteria_text": criteria_text,
            "appointments_text": appointments_text,
            "doctor_full_name": doctor_full_name,
            "clinic_name": clinic_name,
            "appointment_date": appointment_date,
            "specialty": specialty
        })
        
        if result.match_found:
            logger.info(
                f" ... LLM match found: Appointment ID {result.matched_appointment_id} "
                f"(confidence: {result.confidence})"
            )
        else:
            logger.info(" ... LLM found no match")
        
        return result
    
    def _validate_inputs(
        self,
        appointments: List[Dict[str, Any]],
        appointment_info: AppointmentInfoModel
    ) -> None:

        if not appointments:
            raise ValueError("Appointments list cannot be empty")
        
        if not isinstance(appointments, list):
            raise ValueError("Appointments must be a list")
        
        if not appointment_info:
            raise ValueError("Appointment info cannot be None")
        
        has_criteria = any([
            appointment_info.doctor_full_name,
            appointment_info.clinic_name,
            appointment_info.appointment_date,
            appointment_info.specialty
        ])
        
        if not has_criteria:
            raise ValueError(
                "Appointment info must have at least one field (doctor, clinic, date, or specialty)"
            )
    
    def _format_criteria(
        self,
        appointment_info: AppointmentInfoModel
    ) -> str:
        criteria_parts = []
        
        if appointment_info.doctor_full_name:
            criteria_parts.append(f"- Doctor: {appointment_info.doctor_full_name}")
        if appointment_info.clinic_name:
            criteria_parts.append(f"- Clinic: {appointment_info.clinic_name}")
        if appointment_info.appointment_date:
            criteria_parts.append(f"- Date/Time: {appointment_info.appointment_date}")
        if appointment_info.specialty:
            criteria_parts.append(f"- Specialty: {appointment_info.specialty}")
        
        if not criteria_parts:
            return "No specific criteria provided"
        
        return "\n".join(criteria_parts)
    
    def _format_appointments(
        self, 
        appointments: List[Dict[str, Any]]
    ) -> str:
        formatted_parts = []
        
        for idx, appt in enumerate(appointments, 1):
            formatted_appt = self._format_single_appointment(appt, idx)
            formatted_parts.append(formatted_appt)
        
        return "\n".join(formatted_parts)
    
    def _format_single_appointment(
        self,
        appt: Dict[str, Any],
        index: int
    ) -> str:
        try:
            appointment_id = appt.get('id', 'N/A')
            starts_at = appt.get('starts_at', 'N/A')
            ends_at = appt.get('ends_at', 'N/A')
            reason = appt.get('reason', 'N/A')
            status = appt.get('status', 'N/A')
            
            provider = appt.get('provider', {})
            doctor_name = provider.get('full_name', 'N/A')
            specialty = provider.get('specialty', 'N/A')
            
            clinic = appt.get('clinic', {})
            clinic_name = clinic.get('name', 'N/A')
            address = clinic.get('address_line1', 'N/A')
            city = clinic.get('city', 'N/A')
            state = clinic.get('state', 'N/A')
            
            return dedent(f"""
                Appointment {index}:
                - ID: {appointment_id}
                - Date/Time: {starts_at} to {ends_at}
                - Doctor: {doctor_name}
                - Specialty: {specialty}
                - Clinic: {clinic_name}
                - Address: {address}, {city}, {state}
                - Reason: {reason}
                - Status: {status}
                ---
            """).strip()
            
        except Exception as e:
            logger.warning(f"Error formatting appointment {index}: {e}")
            return f"Appointment {index}: [Error formatting details]\n---"
    
    def _build_prompt_template(self) -> PromptTemplate:
        system_prompt = ConversationalQAMessages.appointment_match_system
        human_prompt = ConversationalQAMessages.appointment_match_human
        
        template = self.build_prompt_template(
            system_prompt=system_prompt,
            human_prompt=human_prompt,
            system_input_variables=["criteria_text", "appointments_text"],
            human_input_variables=["doctor_full_name", "clinic_name", "appointment_date", "specialty"]
        )
        
        return template
    
    def _get_fallback_response(self) -> AppointmentMatchModel:
        logger.warning("Returning fallback response: No match")
        
        return AppointmentMatchModel(
            match_found=False,
            confidence=0.0,
            matched_appointment_id=None,
            reasoning="Unable to match appointment due to service error"
        )