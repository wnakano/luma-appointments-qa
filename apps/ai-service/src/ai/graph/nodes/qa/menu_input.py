from datetime import datetime
from textwrap import dedent
from typing import Any, Dict, List
from ...states.qa import QAState, MenuState
from ...services.qa import (
    ResponseService, 
    QueryORMService
)
from ...types.qa import Nodes
from utils import Logger

logger = Logger(__name__)


class MenuNodeInput:
    """Node to present menu options to verified users"""
    
    def __init__(
        self, 
        response_service: ResponseService, 
        query_service: QueryORMService
    ) -> None:
        self.response_service = response_service
        self.query_service = query_service  
    
    def __call__(self, state: QAState) -> QAState:
        """Present menu options to verified user"""
        logger.info("[NODE] Menu Input Node")
        previous_node: str = state.get("current_node", "")
        route: str = state.get("route", "")

        logger.info(
			f"Menu Input - previous_node={previous_node} route={route}"
		)
        patient_record = state.get("user_info_db")
        patient_id = patient_record.get("patient_id")

        appointments = self.query_service.find_appointments_by_patient_id(
            patient_id=patient_id
        )
        appointments_map = {str(idx+1): appointment for idx, appointment in enumerate(appointments)}
        
        logger.info(f"Found appointments for user {patient_id}: {len(appointments)}")

        response_message = self._generate_menu_input_message(
            state=state,
            appointments=appointments
        )
        
        state["current_node"] = Nodes.MENU_INPUT
        
        updated_state = QAState(**{
            **state,
            "assistant_message": response_message,
            "messages": state["messages"] + [response_message],
            "route": "menu_wait",
            "appointments": appointments_map,
            "phase": "menu_selection"
        })
        
        logger.info("Menu presented to user, waiting for selection")
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

    def _generate_menu_input_message(
        self, 
        state: QAState,
        appointments: List[Dict[str, Any]]
    ) -> str:
        """Generate the menu message with available options"""
        user_name = state.get("collected_info", {}).get("name", "")
        menu_text = ""
        current_node = state.get("current_node", "")
        if current_node == Nodes.QUERY_IDENTITY:
            menu_text += f"Great! Your identity has been verified successfully"
            if user_name:
                menu_text += f", {user_name}. How can I help you today?\n\n"
        elif current_node == Nodes.CHECK_USER_SESSION:
            menu_text += f"Welcome back"
            if user_name:
                menu_text += f", {user_name}"
            menu_text += "! How can I help you today?\n\n"

        elif current_node == Nodes.ACTION_APPOINTMENT_LIST:
            assistant_message = state.get("assistant_message", "")
            if assistant_message:
                menu_text += f"{assistant_message}\n\n"
            menu_text += "What would you like to do next?\n\n"

        elif current_node == Nodes.MENU_OUTPUT:
            menu_text += f"Invalid choice. Please try again.\n\n"

        menu_text += "Here are your upcoming appointments:\n\n"
        appointments_text = self._format_appointments(appointments=appointments)
        if not appointments_text:
            menu_text += "You have no appointments scheduled."
        else:
            menu_text += appointments_text
            menu_text += "\n\nPlease enter the number of the appointment you'd like to talk more (confirm or cancel)?"
        
        return menu_text

