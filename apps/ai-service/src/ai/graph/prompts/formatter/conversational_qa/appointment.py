from datetime import datetime
from textwrap import dedent
from typing import Dict, List, Optional, Any, Tuple

from ....types.conversational_qa import IntentType
from ....models.conversational_qa import VerificationRecordModel
from utils import Logger

logger = Logger(__name__)


class AppointmentPromptFormatter:

	INTENT_ACTION_MAP: Dict[IntentType, str] = {
		IntentType.CANCEL_APPOINTMENT: "cancel",
		IntentType.CONFIRM_APPOINTMENT: "confirm",
	}
	DATE_FORMAT = '%B %d, %Y'
	TIME_FORMAT = '%I:%M %p'    
	NO_APPOINTMENTS_MESSAGE = "You have no appointments scheduled."
	
	@staticmethod
	def format_appointments(appointments: List[Dict[str, Any]]) -> str:
		if not appointments:
			return AppointmentPromptFormatter.NO_APPOINTMENTS_MESSAGE
		
		try:
			formatted_parts = []
			
			for idx, appointment in enumerate(appointments, 1):
				formatted_appointment = AppointmentPromptFormatter._format_single_appointment(
					appointment, idx
				)
				formatted_parts.append(formatted_appointment)
			
			return "\n".join(formatted_parts).strip()
			
		except Exception as e:
			logger.error(f"Error formatting appointments: {e}", exc_info=True)
			return "Unable to format appointments. Please try again."
	
	@staticmethod
	def _format_single_appointment(appointment: Dict[str, Any], index: int) -> str:
		try:
			date_str, time_str = AppointmentPromptFormatter._format_datetime(
				appointment.get('starts_at')
			)
			reason = appointment.get('reason', 'Appointment')
			status = appointment.get('status', 'unknown').capitalize()
			provider = appointment.get('provider', {}).get('full_name', 'Unknown')
			specialty = appointment.get('provider', {}).get('specialty', 'N/A')
			clinic_name = appointment.get('clinic', {}).get('name', 'Unknown Clinic')
			
			clinic_address = AppointmentPromptFormatter._format_clinic_address(
				appointment.get('clinic', {})
			)
			
			formatted_text = dedent(f"""
			Appointment {index}. {reason} - {date_str} at {time_str}
			   • Status: {status}
			   • Provider: Dr. {provider} ({specialty})
			   • Location: {clinic_name}
			   • Address: {clinic_address}

			""")
			
			return formatted_text
			
		except Exception as e:
			logger.error(f"Error formatting appointment {index}: {e}")
			return f"Appointment {index}. [Error formatting appointment details]\n\n"
	
	@staticmethod
	def _format_clinic_address(clinic: Dict[str, Any]) -> str:
		address_parts = [
			clinic.get('address_line1'),
			clinic.get('city'),
			f"{clinic.get('state')} {clinic.get('postal_code')}".strip()
		]
		
		address_parts = [part for part in address_parts if part]
		
		if not address_parts:
			return "Address not available"
		
		return ", ".join(address_parts)
	
	@staticmethod
	def generate_confirmation_prompt(
		appointment: Dict[str, Any],
		current_intent: IntentType,
		user_record: Optional[VerificationRecordModel] = None
	) -> str:
		try:

			if current_intent not in AppointmentPromptFormatter.INTENT_ACTION_MAP:
				raise ValueError(
					f"Unsupported intent: {current_intent}. "
					f"Supported intents: {list(AppointmentPromptFormatter.INTENT_ACTION_MAP.keys())}"
				)
			
			provider_name = appointment.get('provider', {}).get('full_name', 'the doctor')
			specialty = appointment.get('provider', {}).get('specialty', 'N/A')
			clinic_name = appointment.get('clinic', {}).get('name', 'the clinic')
			
			date_str, time_str = AppointmentPromptFormatter._format_datetime(
				appointment.get('starts_at')
			)
			intent_string = AppointmentPromptFormatter.INTENT_ACTION_MAP[current_intent]
			
			greeting = AppointmentPromptFormatter._get_personalized_greeting(user_record)
			
			prompt = (
				f"{greeting}do you want to {intent_string} the appointment "
				f"at {clinic_name} on {date_str} at {time_str} "
				f"with Dr. {provider_name} (specialty: {specialty})?"
			)
			
			return prompt
			
		except Exception as e:
			logger.error(f"Error generating confirmation prompt: {e}", exc_info=True)
			raise
	
	@staticmethod
	def _get_personalized_greeting(
		user_record: Optional[VerificationRecordModel]
	) -> str:
		if not user_record or not user_record.full_name:
			return ""
		
		try:
			first_name = user_record.full_name.split()[0]
			return f"Dear {first_name}, "
		except (IndexError, AttributeError) as e:
			logger.warning(f"Could not extract first name from user record: {e}")
			return ""
	
	@staticmethod
	def _format_datetime(datetime_str: Optional[str]) -> Tuple[str, str]:
		if not datetime_str:
			logger.warning("datetime_str is None or empty, using placeholder")
			return "N/A", "N/A"
		
		try:
			# Remove timezone info and parse
			clean_datetime = datetime_str.replace('+00:00', '').replace('Z', '')
			parsed_time = datetime.fromisoformat(clean_datetime)
			
			date_str = parsed_time.strftime(AppointmentPromptFormatter.DATE_FORMAT)
			time_str = parsed_time.strftime(AppointmentPromptFormatter.TIME_FORMAT)
			
			return date_str, time_str
			
		except (ValueError, AttributeError) as e:
			logger.error(f"Failed to parse datetime '{datetime_str}': {e}")
			raise ValueError(f"Invalid datetime format: {datetime_str}")
	
	@staticmethod
	def format_appointment_summary(
		appointment: Dict[str, Any],
		include_address: bool = False
	) -> str:
		try:
			reason = appointment.get('reason', 'Appointment')
			provider = appointment.get('provider', {}).get('full_name', 'Unknown')
			clinic_name = appointment.get('clinic', {}).get('name', 'Unknown Clinic')
			
			date_str, time_str = AppointmentPromptFormatter._format_datetime(
				appointment.get('starts_at')
			)
			
			summary = (
				f"{reason} on {date_str} at {time_str} "
				f"with Dr. {provider} at {clinic_name}"
			)
			
			if include_address:
				address = AppointmentPromptFormatter._format_clinic_address(
					appointment.get('clinic', {})
				)
				summary += f" ({address})"
			
			return summary
			
		except Exception as e:
			logger.error(f"Error formatting appointment summary: {e}")
			return "Appointment details unavailable"
	
	@staticmethod
	def format_action_result(
		intent: IntentType,
		success: bool,
		appointment: Optional[Dict[str, Any]] = None
	) -> str:
		try:
			action = AppointmentPromptFormatter.INTENT_ACTION_MAP.get(
				intent, "processed"
			)
			
			if success:
				if appointment:
					date_str, time_str = AppointmentPromptFormatter._format_datetime(
						appointment.get('starts_at')
					)
					return (
						f"Your appointment on {date_str} at {time_str} "
						f"has been {action}ed successfully."
					)
				else:
					return f"Your appointment has been {action}ed successfully."
			else:
				return (
					f"Unable to {action} your appointment. "
					"Please try again or contact support."
				)
				
		except Exception as e:
			logger.error(f"Error formatting action result: {e}")
			return "Unable to process your request. Please try again."

