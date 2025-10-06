from datetime import datetime

from ...states.conversational_qa import QAState
from ...types.conversational_qa import (
	Nodes,
	Routes, 
	IntentType
)
from utils import Logger

logger = Logger(__name__)

class AskConfirmationNode:
	def __init__(
		self,
	) -> None:
		pass
	
	def __call__(self, state: QAState) -> QAState:
		logger.info("[NODE] AskConfirmationNode")
		appointment_record = state.get("appointment_record")
		appointments = state.get("appointments")
		user_message = state.get("user_message")
		user_record = state.get("user_record")
		current_intent = state.get("current_intent")
		messages = state.get("messages", [])
		
		appointment_id = appointment_record.appointment_id
		appointment = [appt for appt in appointments if str(appointment_id) == str(appt['id'])][0]
		reason = appointment['reason']
		status = appointment['status'].capitalize()
		provider = appointment['provider']['full_name']
		specialty = appointment['provider']['specialty']
		clinic_name = appointment['clinic']['name']

		start_time = datetime.fromisoformat(appointment['starts_at'].replace('+00:00', ''))
		
		date_str = start_time.strftime('%B %d, %Y')
		time_str = start_time.strftime('%I:%M %p')
		
		ask_prompt = ""	
		user_name = ""
		
		if current_intent == IntentType.CANCEL_APPOINTMENT:
			intent_string = "cancel"
		elif current_intent == IntentType.CONFIRM_APPOINTMENT:
			intent_string = "confirm"

		if user_record:
			full_name = user_record.full_name
			user_name = full_name.split(" ")[0]
			ask_prompt += f"Dear {user_name}, "
		
		ask_prompt += (
			f"do you want to {intent_string} the appointment"
			f"at {clinic_name} at {date_str} {time_str} with Dr. {provider} (specialty: {specialty})?"
		)

		state["current_node"] = Nodes.ASK_CONFIRMATION
		state["messages"] = messages + [
			{
				"user_message": user_message,
				"system_message": ask_prompt
			}
		]

		return state

