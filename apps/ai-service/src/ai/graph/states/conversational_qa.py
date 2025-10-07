from typing import (
    Any, 
    Dict,
    Final,
    List, 
    Literal,
    Optional, 
    TypedDict,
    Union 
)
from ..types.conversational_qa import (
    IntentType,
    Nodes
)
from ..models.conversational_qa import (
    AppointmentInfoModel,
    AppointmentRecordModel,
    VerificationInfoModel,
    VerificationRecordModel,
    AppointmentConfirmationResponse
)

class MenuState(TypedDict):
    assistant_message: Optional[str]
    menu_options: Optional[Dict[str, Dict[str, str]]]
    selected_action: Optional[str]
    selected_menu_choice: Optional[str]
    phase: Optional[str]


class QAState(TypedDict):
    # request_id: str
    session_id: Optional[str]
    user_message: str
    history: List[Dict[str, Any]]
    messages: List[Dict[str, str]]
    
    current_node: Nodes
    current_intent: IntentType
    intent_confidence: float

    is_verified: bool
    appointments: List[Dict[str, Any]] = []

    full_name: str
    phone_number: str
    date_of_birth: str
    user_id: str = ""

    user_info: Union[VerificationInfoModel, None]
    user_record: Union[VerificationRecordModel, None]
    user_request_counter: int = 0

    appointment_info: Union[AppointmentInfoModel, None] = None
    appointment_record: Union[AppointmentRecordModel, None] = None
    appointment_request_counter: int = 0
    
    confirmation_intent: Union[AppointmentConfirmationResponse, None] = None
    
    verification_step: str  # "name", "phone", "dob", "complete", "verify"
    user_verified: bool
    collected_info: Dict[str, str]  # {"name": "", "phone": "", "dob": ""}
    
    route: str

class StateKeys:
    """Constants for QAState dictionary keys."""
    
    SESSION_ID: Final[str] = "session_id"
    USER_MESSAGE: Final[str] = "user_message"
    HISTORY: Final[str] = "history"
    MESSAGES: Final[str] = "messages"
    
    CURRENT_NODE: Final[str] = "current_node"
    CURRENT_INTENT: Final[str] = "current_intent"
    INTENT_CONFIDENCE: Final[str] = "intent_confidence"
    ROUTE: Final[str] = "route"
    
    IS_VERIFIED: Final[str] = "is_verified"
    USER_VERIFIED: Final[str] = "user_verified"
    VERIFICATION_STEP: Final[str] = "verification_step"
    COLLECTED_INFO: Final[str] = "collected_info"
    
    FULL_NAME: Final[str] = "full_name"
    PHONE_NUMBER: Final[str] = "phone_number"
    DATE_OF_BIRTH: Final[str] = "date_of_birth"
    USER_ID: Final[str] = "user_id"
    USER_INFO: Final[str] = "user_info"
    USER_RECORD: Final[str] = "user_record"
    USER_REQUEST_COUNTER: Final[str] = "user_request_counter"
    
    APPOINTMENTS: Final[str] = "appointments"
    APPOINTMENT_INFO: Final[str] = "appointment_info"
    APPOINTMENT_RECORD: Final[str] = "appointment_record"
    APPOINTMENT_REQUEST_COUNTER: Final[str] = "appointment_request_counter"
    CONFIRMATION_INTENT: Final[str] = "confirmation_intent"