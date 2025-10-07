from datetime import datetime
from typing import Dict, List, Optional

from ...states.conversational_qa import QAState, StateKeys
from ...types.conversational_qa import (
	Nodes,
	MessageKeys, 
	IntentType
)
from ...models.conversational_qa import AppointmentInfoModel, VerificationRecordModel
from utils import Logger

logger = Logger(__name__)


class AskConfirmationNode:

	INTENT_ACTION_MAP: Dict[IntentType, str] = {
		IntentType.CANCEL_APPOINTMENT: "cancel",
		IntentType.CONFIRM_APPOINTMENT: "confirm",
	}
	
	def __call__(self, state: QAState) -> QAState:
		try:
			logger.info("[NODE] AskConfirmationNode")
			
			appointment_record: Optional[AppointmentInfoModel] = state.get(StateKeys.APPOINTMENT_RECORD)
			appointments: Optional[List[Dict]] = state.get(StateKeys.APPOINTMENTS)
			user_message: str = state.get(StateKeys.USER_MESSAGE, "")
			user_record: Optional[VerificationRecordModel] = state.get(StateKeys.USER_RECORD)
			current_intent: Optional[IntentType] = state.get(StateKeys.CURRENT_INTENT)
			messages: List[Dict] = state.get(StateKeys.MESSAGES, [])
			
			self._validate_state(appointment_record, appointments, current_intent)
			
			appointment = self._find_appointment(
				appointments, 
				appointment_record.appointment_id
			)
			
			ask_prompt = self._generate_confirmation_prompt(
				appointment=appointment,
				user_record=user_record,
				current_intent=current_intent
			)
			
			state[StateKeys.CURRENT_NODE] = Nodes.ASK_CONFIRMATION
			state[StateKeys.MESSAGES] = messages + [
				{
					MessageKeys.USER_MESSAGE: user_message,
					MessageKeys.SYSTEM_MESSAGE: ask_prompt
				}
			]
			
			logger.info(f" ... Generated confirmation prompt for intent: {current_intent}")
			
			return state
			
		except Exception as e:
			logger.error(f"Error in AskConfirmationNode: {e}", exc_info=True)
			raise
	
	def _validate_state(
		self,
		appointment_record: Optional[AppointmentInfoModel],
		appointments: Optional[List[Dict]],
		current_intent: Optional[IntentType]
	) -> None:
		if not appointment_record:
			raise ValueError("appointment_record is required but not found in state")
		
		if not appointments:
			raise ValueError("appointments list is required but not found in state")
		
		if not current_intent:
			raise ValueError("current_intent is required but not found in state")
		
		if current_intent not in self.INTENT_ACTION_MAP:
			raise ValueError(
				f"Unsupported intent: {current_intent}. "
				f"Supported intents: {list(self.INTENT_ACTION_MAP.keys())}"
			)
	
	def _find_appointment(
		self, 
		appointments: List[Dict], 
		appointment_id: str
	) -> Dict:
		matching_appointments = [
			appt for appt in appointments 
			if str(appt.get('id')) == str(appointment_id)
		]
		
		if not matching_appointments:
			logger.error(f"Appointment with ID {appointment_id} not found in appointments list")
			raise ValueError(f"Appointment with ID {appointment_id} not found")
		
		if len(matching_appointments) > 1:
			logger.warning(f"Multiple appointments found with ID {appointment_id}, using first match")
		
		return matching_appointments[0]
	
	def _generate_confirmation_prompt(
		self,
		appointment: Dict,
		user_record: Optional[VerificationRecordModel],
		current_intent: IntentType
	) -> str:
		provider_name = appointment.get('provider', {}).get('full_name', 'the doctor')
		specialty = appointment.get('provider', {}).get('specialty', 'N/A')
		clinic_name = appointment.get('clinic', {}).get('name', 'the clinic')
		
		date_str, time_str = self._format_appointment_datetime(
			appointment.get('starts_at')
		)
		
		intent_string = self.INTENT_ACTION_MAP[current_intent]
		
		ask_prompt = ""
		if user_record and user_record.full_name:
			first_name = user_record.full_name.split()[0]
			ask_prompt = f"Dear {first_name}, "
		
		ask_prompt += (
			f"do you want to {intent_string} the appointment "
			f"at {clinic_name} on {date_str} at {time_str} "
			f"with Dr. {provider_name} (specialty: {specialty})?"
		)
		
		return ask_prompt
	
	def _format_appointment_datetime(self, starts_at: Optional[str]) -> tuple[str, str]:
		if not starts_at:
			logger.warning("starts_at is None or empty, using placeholder")
			return "N/A", "N/A"
		
		try:
			# Remove timezone info and parse
			clean_datetime = starts_at.replace('+00:00', '').replace('Z', '')
			start_time = datetime.fromisoformat(clean_datetime)
			
			date_str = start_time.strftime('%B %d, %Y')
			time_str = start_time.strftime('%I:%M %p')
			
			return date_str, time_str
			
		except (ValueError, AttributeError) as e:
			logger.error(f"Failed to parse datetime '{starts_at}': {e}")
			raise ValueError(f"Invalid datetime format: {starts_at}")