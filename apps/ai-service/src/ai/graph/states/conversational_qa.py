from typing import (
    Any, 
    Dict,
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
    VerificationRecordModel
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

    appointment_info: Union[AppointmentInfoModel, None] = None
    appointment_record: Union[AppointmentRecordModel, None] = None
    
    verification_step: str  # "name", "phone", "dob", "complete", "verify"
    user_verified: bool
    collected_info: Dict[str, str]  # {"name": "", "phone": "", "dob": ""}
    
    route: str
