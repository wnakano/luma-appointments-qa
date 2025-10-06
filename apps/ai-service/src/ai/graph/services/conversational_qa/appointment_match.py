from langchain.prompts import PromptTemplate 
from textwrap import dedent
from typing import Any, Dict, List, Optional

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
		):
		logger.info("[SERVICE] AppointmentMatchService")

		doctor_full_name = appointment_info.doctor_full_name
		clinic_name = appointment_info.clinic_name
		appointment_date = appointment_info.appointment_date
		specialty = appointment_info.specialty

		criteria_text = self._get_criteria_text(appointment_info=appointment_info)
		appointments_text = self._get_appointments_text(appointments=appointments)
		template = self._build_prompt_template()
		chain = self.build_structured_chain(
			template=template,
			schema=AppointmentMatchModel
		)
		
		try:
			result: AppointmentMatchModel = chain.invoke(
				{
					"criteria_text": criteria_text,
					"appointments_text": appointments_text,
					"doctor_full_name": doctor_full_name,
					"clinic_name": clinic_name,
					"appointment_date": appointment_date,
					"specialty": specialty
				}
			)
			return result
		
		except Exception as e:
			logger.error(f"[Service] Appointment Match ERROR: {e}")
			return self._get_fallback()
	
	def _get_criteria_text(
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
		
		criteria_text = "\n".join(criteria_parts) if criteria_parts else "No specific criteria provided"
		return criteria_text
	
	def _get_appointments_text(
		self, 
		appointments: List[Dict[str, Any]]
	) -> str:
		appointments_text = ""
		for idx, appt in enumerate(appointments, 1):
			appointments_text += dedent(f"""
				Appointment {idx}:
				- ID: {appt['id']}
				- Date/Time: {appt['starts_at']} to {appt['ends_at']}
				- Doctor: {appt['provider']['full_name']}
				- Specialty: {appt['provider']['specialty']}
				- Clinic: {appt['clinic']['name']}
				- Address: {appt['clinic']['address_line1']}, {appt['clinic']['city']}, {appt['clinic']['state']}
				- Reason: {appt['reason']}
				- Status: {appt['status']}
				---
				"""
			)
		return appointments_text
	
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

	def _get_fallback(self) -> AppointmentMatchModel:
		"""
		Return a safe fallback intent when classification fails.
		
		Args:
			user_message: The original user message
			
		Returns:
			ConversationIntent with GENERAL_QA intent and low confidence
		"""
		logger.warning("Returning fallback: APPOINTMENT_MATCH")
		
		return AppointmentMatchModel(
			match_found=False,
			confidence=0.0,
			matched_appointment_id=None,
			reasoning="Error"
		)