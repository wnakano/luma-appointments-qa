from datetime import datetime

from ...states.conversational_qa import QAState, StateKeys
from ...types.conversational_qa import (
	Nodes,
	MessageKeys, 
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
		appointment_record = state.get(StateKeys.APPOINTMENT_INFO)
		appointments = state.get(StateKeys.APPOINTMENTS)
		user_message = state.get(StateKeys.USER_MESSAGE)
		user_record = state.get(StateKeys.USER_RECORD)
		current_intent = state.get(StateKeys.CURRENT_INTENT)
		messages = state.get(StateKeys.MESSAGES, [])
		
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

		state[StateKeys.CURRENT_NODE] = Nodes.ASK_CONFIRMATION
		state[StateKeys.MESSAGES] = messages + [
			{
				MessageKeys.USER_MESSAGE: user_message,
				MessageKeys.SYSTEM_MESSAGE: ask_prompt
			}
		]

		return state

