from typing import List, Optional

from ...states.conversational_qa import QAState, StateKeys
from ...types.conversational_qa import (
	Nodes,
	MessageKeys
)
from ...models.conversational_qa import VerificationRecordModel
from ...prompts.formatter.conversational_qa import AppointmentPromptFormatter

from utils import Logger

logger = Logger(__name__)


class ListAppointmentsNode:
	GREETING_TEMPLATE = "Dear {name}, your upcoming appointments are:\n\n"
	NO_GREETING_TEMPLATE = "Your upcoming appointments are:\n\n"
	
	def __init__(self, voice_mode: bool = False) -> None:
		self.voice_mode = voice_mode
	
	def __call__(self, state: QAState) -> QAState:
		try:
			logger.info("[NODE] ListAppointmentsNode")
			
			appointments = state.get(StateKeys.APPOINTMENTS, [])
			messages = state.get(StateKeys.MESSAGES, [])
			user_message = state.get(StateKeys.USER_MESSAGE, "")
			user_record = state.get(StateKeys.USER_RECORD)
			
			appointment_list_message = self._generate_appointment_list_message(
				appointments=appointments,
				user_record=user_record
			)
			
			state[StateKeys.CURRENT_NODE] = Nodes.LIST_APPOINTMENTS
			state[StateKeys.MESSAGES] = messages + [
				{
					MessageKeys.USER_MESSAGE: user_message,
					MessageKeys.SYSTEM_MESSAGE: appointment_list_message
				}
			]
			
			logger.info(f" ... Listed {len(appointments)} appointment(s)")
			
			return state
			
		except Exception as e:
			logger.error(f"Error in ListAppointmentsNode: {e}", exc_info=True)
			raise
	
	def _generate_appointment_list_message(
		self,
		appointments: List,
		user_record: Optional[VerificationRecordModel]
	) -> str:
		greeting = self._get_greeting(user_record)

		if self.voice_mode:
			formatted_appointments = AppointmentPromptFormatter.format_appointments_for_voice(
				appointments=appointments
			)
		else:
			formatted_appointments = AppointmentPromptFormatter.format_appointments(
				appointments=appointments
			)
		
		return greeting + formatted_appointments
	
	def _get_greeting(self, user_record: Optional[VerificationRecordModel]) -> str:
		if not user_record or not user_record.full_name:
			return self.NO_GREETING_TEMPLATE
		
		try:
			first_name = user_record.full_name.split()[0]
			return self.GREETING_TEMPLATE.format(name=first_name)
		except (IndexError, AttributeError) as e:
			logger.warning(f"Could not extract first name from user record: {e}")
			return self.NO_GREETING_TEMPLATE