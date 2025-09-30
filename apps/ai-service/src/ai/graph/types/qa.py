from enum import Enum, IntEnum
from typing import Dict, Optional


class MenuType(str, Enum):
	USER_VERIFICATION: str = "USER_VERIFICATION"
	LIST: str = "LIST"
	CONFIRM: str = "CONFIRM"
	CANCEL: str = "CANCEL"
	RESCHEDULE: str = "RESCHEDULE"
	ROUTING: str = "ROUTING"


class IdentificationState(str, Enum):
	UNKNOWN = "UNKNOWN"
	MISSING = "MISSING"
	VERIFIED = "VERIFIED"
	IDENTIFIED = "IDENTIFIED"


class FlowPhase(Enum):
    INITIAL = "initial"
    COLLECTION = "collection"
    VERIFICATION = "verification"
    VERIFIED = "verified"
    COMPLETED = "completed"
    MENU = "menu"
    ACTION_PROCESSING = "action_processing"

class Nodes(str, Enum):    
    CHECK_USER_SESSION = "CHECK_USER_SESSION"
    PROCESS_USER_INPUT = "PROCESS_USER_INPUT"
    COLLECT_USER_INFO = "COLLECT_USER_INFO"
    HANDLE_INVALID_INPUT = "HANDLE_INVALID_INPUT"
    VERIFY_IDENTITY = "VERIFY_IDENTITY"
    QUERY_IDENTITY = "QUERY_IDENTITY"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"
    MENU_INPUT = "MENU_INPUT"
    MENU_OUTPUT = "MENU_OUTPUT"
    ACTION_APPOINTMENT_LIST = "ACTION_APPOINTMENT_LIST"


class Routes(str, Enum):
	UNKNOWN: str = "UNKNOWN"
	WAIT: str = "WAIT"
	# CHECK_USER_SESSION
	MISSING: str = "MISSING"
	VERIFIED: str = "VERIFIED"
	IDENTIFIED: str = "IDENTIFIED"
	# PROCESS_USER_INPUT
	COLLECT_NEXT: str = "COLLECT_NEXT"
	VERIFY: str = "VERIFY"
	# PROCESS_USER_INPUT
	PROCESS_USER_INPUT: str = "PROCESS_USER_INPUT"
	# VERIFY_IDENTITY
	RETRY: str = "RETRY"
	FAILED: str = "FAILED"
	# QUERY_IDENTITY
	MATCH: str = "MATCH"
	NOT_MATCH: str = "NOT_MATCH"
	# MENU_OUTPUT
	WAIT_MENU_SELECTION: str = "WAIT_MENU_SELECTION"
	WAIT_APPOINTMENT_ACTION: str = "WAIT_APPOINTMENT_ACTION"
	WRONG_APPOINTMENT_CHOICE: str = "WRONG_APPOINTMENT_CHOICE"
	# ACTION_APPOINTMENT_LIST
	WRONG_ACTION_CHOICE: str = "WRONG_ACTION_CHOICE"
	CORRECT_APPOINTMENT_ACTION: str = "CORRECT_APPOINTMENT_ACTION"
	ACTION_COMPLETED: str = "ACTION_COMPLETED"
	INVALID_INPUT: str = "INVALID_INPUT"
	

class UserSession:
	def __init__(self):
		self.name: Optional[str] = None
		self.phone_number: Optional[str] = None
		self.verified: bool = False
		self.state: IdentificationState = IdentificationState.UNKNOWN
		self.context: Dict[str, str] = {}
		self.missing = []
	
	def to_dict(self) -> Dict[str, str]:
		attrs = self.__dict__.copy()
		for attr, value in attrs.items():
			if isinstance(value, Enum):
				attrs[attr] = value.value
		return attrs
	
	def update_state(self) -> None:
		missing = []

		if not (self.name and self.name.strip()):
			missing.append("name")
		if not (self.phone_number and self.phone_number.strip()):
			missing.append("mobile")
		if not (self.email and self.email.strip()):
			missing.append("email")
		

		self.verified = len(missing) == 0

		self.state = IdentificationState.IDENTITY_VERIFIED \
			if IdentificationState.VERIFIED \
				else IdentificationState.VERIFYING
		
		self.missing = missing