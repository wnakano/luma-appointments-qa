from enum import Enum, IntEnum
from typing import Dict, Optional



class IntentType(str, Enum):
	"""Enumeration of all possible user intents"""
	
	GENERAL_QA: str = "general_qa"
	LIST_APPOINTMENTS: str = "list_appointments"
	CONFIRM_APPOINTMENT: str = "confirm_appointment"
	CANCEL_APPOINTMENT: str = "cancel_appointment"
	USER_INFORMATION: str = "user_information"
	APPOINTMENT_INFORMATION: str = "appointment_information"
	
	def __str__(self):
		return self.value
	

class FlowPhase(str, Enum):
	INITIAL: str = "INITIAL"
	COLLECTION: str = "COLLECTION"
	VERIFICATION: str = "VERIFICATION"
	VERIFIED: str = "VERIFIED"
	COMPLETED: str = "COMPLETED"
	MENU: str = "MENU"
	ACTION_PROCESSING: str = "ACTION_PROCESSING"


class Nodes(str, Enum):    
	CONVERSATION_MANAGER: str = "CONVERSATION_MANAGER"
	QA_ANSWER: str = "QA_ANSWER"
	VERIFICATION_GATE: str = "VERIFICATION_GATE"
	VERIFICATION_PATIENT: str = "VERIFICATION_PATIENT"
	VERIFICATION_APPOINTMENT: str = "VERIFICATION_APPOINTMENT"
	CLARIFICATION: str = "CLARIFICATION"
	ACTION_ROUTER: str = "ACTION_ROUTER"
	WAIT_APPOINTMENT: str = "WAIT_APPOINTMENT"
	LIST_APPOINTMENTS: str = "LIST_APPOINTMENTS"
	CONFIRM_APPOINTMENTS: str = "CONFIRM_APPOINTMENTS"
	CANCEL_APPOINTMENTS: str = "CANCEL_APPOINTMENTS"
	ASK_CONFIRMATION: str = "ASK_CONFIRMATION"
	PROCESS_CONFIRMATION: str = "PROCESS_CONFIRMATION"
	GENERAL_HELP: str = "GENERAL_HELP"
	ACTION_RESPONSE: str = "ACTION_RESPONSE"
	ACTION_END: str = "ACTION_END"


class Routes(str, Enum):
	ACTION_APPOINTMENT: str = "ACTION_APPOINTMENT"
	ACTION_QA: str = "QA"
	USER_VERIFICATION: str = "USER_VERIFICATION" 
	APPOINTMENT_VERIFICATION: str = "APPOINTMENT_VERIFICATION" 
	VERIFIED: str = "VERIFIED"
	NOT_VERIFIED: str = "NOT_VERIFIED"
	INTENT_WAIT: str = "INTENT_WAIT"
	INTENT_LIST: str = "INTENT_LIST"
	INTENT_CONFIRM: str = "INTENT_CONFIRM"
	INTENT_CANCEL: str = "INTENT_CANCEL"
	COLLECTING_DATA: str = "COLLECTING_DATA"
	DATA_COLLECTED: str = "DATA_COLLECTED"
	ACTION_CONFIRMED: str = "ACTION_CONFIRMED"
	ACTION_REJECTED: str = "ACTION_REJECTED"
	ACTION_UNCLEAR: str = "ACTION_UNCLEAR" 

	
class DBAppointmentStatus(str, Enum):
	SCHEDULED: str = "scheduled"
	CONFIRMED: str = "confirmed"
	CANCELED_BY_PATIENT: str = "canceled_by_patient"

	def __str__(self):
		return self.value


class ConfirmationIntent(str, Enum):
	"""Enumeration of possible confirmation intents"""
	CONFIRM: str = "confirm"
	REJECT: str = "reject"
	UNCLEAR: str = "unclear"


class MessageKeys:
    """Constants for message dictionary keys."""
    USER_MESSAGE = "user_message"
    SYSTEM_MESSAGE = "system_message"


# class UserSession:
# 	def __init__(self):
# 		self.name: Optional[str] = None
# 		self.phone_number: Optional[str] = None
# 		self.verified: bool = False
# 		self.state: IdentificationState = IdentificationState.UNKNOWN
# 		self.context: Dict[str, str] = {}
# 		self.missing = []
	
# 	def to_dict(self) -> Dict[str, str]:
# 		attrs = self.__dict__.copy()
# 		for attr, value in attrs.items():
# 			if isinstance(value, Enum):
# 				attrs[attr] = value.value
# 		return attrs
	
# 	def update_state(self) -> None:
# 		missing = []

# 		if not (self.name and self.name.strip()):
# 			missing.append("name")
# 		if not (self.phone_number and self.phone_number.strip()):
# 			missing.append("mobile")
# 		if not (self.email and self.email.strip()):
# 			missing.append("email")
		

# 		self.verified = len(missing) == 0

# 		self.state = IdentificationState.IDENTITY_VERIFIED \
# 			if IdentificationState.VERIFIED \
# 				else IdentificationState.VERIFYING
		
# 		self.missing = missing