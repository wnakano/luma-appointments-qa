from datetime import datetime
from textwrap import dedent
from typing import Any, Dict, List

from ...states.conversational_qa import QAState, StateKeys
from ...types.conversational_qa import (
	Nodes,
	Routes, 
	IntentType
)
from utils import Logger

logger = Logger(__name__)


class ListAppointmentsNode:
	def __init__(
		self,
	) -> None:
		pass
	
	def __call__(self, state: QAState) -> QAState:
		logger.info("[NODE] ListAppointmentsNode")
		appointments = state.get(StateKeys.APPOINTMENTS, [])
		messages = state.get(StateKeys.MESSAGES, [])
		user_message = state.get(StateKeys.USER_MESSAGE, "")

		user_record = state.get(StateKeys.USER_RECORD, None)
		user_name = ""
		if user_record:
			full_name = user_record.full_name
			user_name = full_name.split(" ")[0]
		
		appointment_list_output_message = self._generate_appointment_list_output_message(
			user_name=user_name,
			appointments=appointments
		)

		state[StateKeys.CURRENT_NODE] = Nodes.LIST_APPOINTMENTS
		state[StateKeys.MESSAGES] = messages + [
			{
				"user_message": user_message,
				"system_message": appointment_list_output_message
			}
		]
		return state

	def _format_appointments(self, appointments: List[Dict[str, Any]]) -> str:
		"""
		Format appointments data into a user-friendly string display.
		
		Args:
			appointments (list): List of appointment dictionaries from the database
			
		Returns:
			str: Formatted string with numbered appointments
		"""
		if not appointments:
			return "You have no appointments scheduled."
		
		formatted_text = ""
		
		for idx, apt in enumerate(appointments, 1):
			start_time = datetime.fromisoformat(apt['starts_at'].replace('+00:00', ''))
			
			date_str = start_time.strftime('%B %d, %Y')
			time_str = start_time.strftime('%I:%M %p')
	
			reason = apt['reason']
			status = apt['status'].capitalize()
			provider = apt['provider']['full_name']
			specialty = apt['provider']['specialty']
			clinic_name = apt['clinic']['name']
			clinic_address = f"{apt['clinic']['address_line1']}, {apt['clinic']['city']}, {apt['clinic']['state']} {apt['clinic']['postal_code']}"
			
			formatted_text += dedent(f"""
			Appointment {idx}. {reason} - {date_str} at {time_str}
			   • Status: {status}
			   • Provider: Dr. {provider} ({specialty})
			   • Location: {clinic_name}
			   • Address: {clinic_address}

			""")
	
		return formatted_text.strip()

	def _format_appointments_to_voice(self, appointments: List[Dict[str, Any]]) -> str:
		"""
		Format appointments data into a user-friendly string display.
		
		Args:
			appointments (list): List of appointment dictionaries from the database
			
		Returns:
			str: Formatted string with numbered appointments
		"""
		if not appointments:
			return "You have no appointments scheduled."
		
		formatted_text = ""
		
		for idx, apt in enumerate(appointments, 1):
			start_time = datetime.fromisoformat(apt['starts_at'].replace('+00:00', ''))
			
			date_str = start_time.strftime('%B %d, %Y')
			time_str = start_time.strftime('%I:%M %p')
	
			reason = apt['reason']
			status = apt['status'].capitalize()
			provider = apt['provider']['full_name']
			specialty = apt['provider']['specialty']
			clinic_name = apt['clinic']['name']
			clinic_address = f"{apt['clinic']['address_line1']}, {apt['clinic']['city']}, {apt['clinic']['state']} {apt['clinic']['postal_code']}"
			
			formatted_text += dedent(f"""
			Appointment {idx}. {reason} - {date_str} at {time_str} at {clinic_name} with Dr. {provider} (specialty: {specialty}) is {status}

			""")
	
		return formatted_text.strip()
	
	def _generate_appointment_list_output_message(
		self,
		user_name: str,
		appointments: Dict[str, Dict[str, Any]]
	) -> str:
		"""Generate the menu message with available options"""
		menu_text = ""
		if user_name:
			menu_text += f"Dear {user_name}, "

		menu_text += f"yours upcomings appointments are:\n\n"
		appointments_text = self._format_appointments(appointments=appointments)
		menu_text += appointments_text
		return menu_text
