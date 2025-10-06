from langchain.prompts import PromptTemplate 
from typing import Any, Dict, List, Optional

from ...models.conversational_qa import AppointmentInfoModel
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



class ClarificationAppointmentService:
	def __init__(self) -> None:
		pass

	def run(
		self,
		appointment_info: AppointmentInfoModel,
	) -> str:
		logger.info("[SERVICE] ClarificationAppointmentService")

		info_appointment_keys = ["doctor_full_name", "clinic_name", "appointment_date", "specialty"]
		if not appointment_info:
			missing_info = info_appointment_keys.copy()
		else:
			missing_info = [key for key in info_appointment_keys if not getattr(appointment_info, key, None)]

		system_prompt = ConversationalQAMessages.base_clarification_appointment_system
		missing_info_human = [info.replace("_", " ") for info in missing_info]
		system_prompt += ", ".join(missing_info_human) 
		return system_prompt

