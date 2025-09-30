from datetime import datetime
from textwrap import dedent
from typing import Any, Dict, List
from ...states.qa import QAState
from ...services.qa import (
    ResponseService, 
    QueryORMService
)
from ...types.qa import Nodes, Routes
from utils import Logger

logger = Logger(__name__)


class MenuNodeOutput:
    """Node to process user's menu selection and route to appropriate action"""
    
    def __init__(
        self, 
        response_service: ResponseService,
        query_service: QueryORMService
        ):
        self.response_service = response_service
        self.query_service = query_service  
        self.options = {
            "1": "Confirm the appointment",
            "2": "Cancel the appointment",
            "3": "Return to the appointments menu"
        }
    
    def __call__(self, state: QAState) -> QAState:
        """Process user's menu selection"""
        user_message = state.get("user_message", "").strip()
        logger.info(f"Processing menu selection: '{user_message}'")
        appointments = state.get("appointments")
        possible_options = list(appointments.keys())
        appointment = None
        state["current_node"] = Nodes.MENU_OUTPUT
        if user_message in possible_options:
            appointment = appointments[user_message]
            
        if appointment:
            message = self._generate_menu_output_message(appointment=appointment)
            updated_state = QAState(**{
                **state,
                "assistant_message": message,
                "messages": state["messages"] + [message],
                "selected_appointment": appointment,
                "route": Routes.WAIT_APPOINTMENT_ACTION,
                "phase": "action_processing"
            })
            return updated_state
        
        updated_state = QAState(**{
            **state,
            "messages": state["messages"],
            "assistant_message": "Invalid choice. Please try again.",
            "selected_appointment": appointment,
            "route": Routes.WRONG_APPOINTMENT_CHOICE,
            "phase": "action_processing"
        })
        return updated_state
        
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
            **{idx}. {reason} - {date_str} at {time_str}**
               • Status: {status}
               • Provider: Dr. {provider} ({specialty})
               • Location: {clinic_name}
               • Address: {clinic_address}

            """)
    
        return formatted_text.strip()
    
    def _generate_menu_output_message(
        self, 
        appointment: Dict[str, Dict[str, Any]]
    ) -> str:
        """Generate the menu message with available options"""

        menu_text = f"Regarding the upcoming appointment:\n\n"
        appointments_text = self._format_appointments(appointments=[appointment])
        menu_text += appointments_text
        menu_text += "\n\nDo you want to:"
        for idx, option in self.options.items():
            menu_text += f"\n**  {idx}. {option}**"
        menu_text += "\n\nPlease enter the number of your choice (1, 2, or 3)."
        return menu_text
    