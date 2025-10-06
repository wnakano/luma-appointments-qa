from langchain.prompts import PromptTemplate 
from typing import Any, Dict, List, Optional

from ...models.conversational_qa import (
	AppointmentRecordModel, 
	UserIntentModel,
	VerificationRecordModel,
	VerificationInfoModel,
	AppointmentInfoModel
	
)
from ...types.conversational_qa import (
	IntentType, 
	ConfirmationIntent,
	Routes
)
from ...states.conversational_qa import QAState	
from ...models.conversational_qa import AppointmentConfirmationResponse
from ...prompts.templates.conversational_qa import ConversationalQAMessages
from ..llm import LLMService

from utils import Logger

logger = Logger(__name__)



class ClarificationService: #(LLMService):
	def __init__(self) -> None:
		# super().__init__(model=model, temp=temp)
		pass

	def user_run(
		self,
		verification_info: VerificationInfoModel,
	) -> str:
		logger.info("[SERVICE] ClarificationService.user_run")

		info_patient_keys = ["full_name", "phone_number", "date_of_birth"]
		if not verification_info:
			missing_info = info_patient_keys.copy()
		else:
			missing_info = [key for key in info_patient_keys if not getattr(verification_info, key, None)]

		system_prompt = ConversationalQAMessages.base_clarification_user_system
		missing_info_human = [info.replace("_", " ") for info in missing_info]
		system_prompt += ", ".join(missing_info_human) 
		return system_prompt

	def appointment_run(
		self,
		appointment_info: AppointmentInfoModel,
	) -> str:
		logger.info("[SERVICE] ClarificationService.appointment_run")

		info_appointment_keys = ["doctor_full_name", "clinic_name", "appointment_date", "specialty"]
		if not appointment_info:
			missing_info = info_appointment_keys.copy()
		else:
			missing_info = [key for key in info_appointment_keys if not getattr(appointment_info, key, None)]

		system_prompt = ConversationalQAMessages.base_clarification_appointment_system
		missing_info_human = [info.replace("_", " ") for info in missing_info]
		system_prompt += ", ".join(missing_info_human) 
		return system_prompt

	def appointment_wait(
		self,
		appointment_info: AppointmentInfoModel,
	) -> str:
		logger.info("[SERVICE] ClarificationService.appointment_wait")

		system_prompt = ConversationalQAMessages.base_clarification_appointment_wait_system
		return system_prompt
