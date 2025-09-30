from typing import (
    Any, 
    Dict,
    List, 
    Literal,
    Optional, 
    TypedDict, 
)
from ..types.qa import (
    MenuType,
    IdentificationState,
    Nodes
)

class MenuState(TypedDict):
    assistant_message: Optional[str]
    menu_options: Optional[Dict[str, Dict[str, str]]]
    selected_action: Optional[str]
    selected_menu_choice: Optional[str]
    phase: Optional[str]


class QAState(TypedDict):
    # request_id: str
    user_message: str
    session_id: Optional[str]
    history: List[Dict[str, Any]]
    messages: List[str]
    
    verification_step: str  # "name", "phone", "dob", "complete", "verify"
    user_verified: bool
    collected_info: Dict[str, str]  # {"name": "", "phone": "", "dob": ""}

    user_info: Optional[Dict[str, str]] = {}
    user_info_db: Optional[Dict[str, str]]  = {}
    
    current_node: Nodes
    route: str

    assistant_message: Optional[str]
    menu_options: Optional[Dict[str, Dict[str, str]]]
    appointments: Optional[Dict[str, Dict[str, str]]]
    selected_appointment: Optional[Dict[str, str]]
    selected_action: Optional[str]
    selected_menu_choice: Optional[str]
    phase: Optional[str]

    menu: Optional[MenuState]
    error_message: Optional[str]
    retry_count: Optional[int]