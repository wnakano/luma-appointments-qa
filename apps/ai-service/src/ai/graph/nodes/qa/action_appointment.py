from datetime import datetime
from textwrap import dedent
from typing import Any, Dict, List
from ...states.qa import QAState, MenuState
from ...services.qa import (
    ResponseService, 
    QueryORMService
)
from ...types.qa import Nodes, Routes
from utils import Logger

logger = Logger(__name__)



class ActionAppointmentNode:
    """Node to handle appointment-related actions based on user input."""

    def __init__(
        self,
        response_service: ResponseService,
        query_service: QueryORMService
    ) -> None:
        self.response_service = response_service
        self.query_service = query_service
        
        self.valid_actions = {
            "1": "confirm_appointment",
            "2": "cancel_appointment",
            "3": "list_appointments"
        }

    def __call__(self, state: QAState) -> QAState:
        """Present menu options to verified user"""
        logger.info("[NODE] Action Appointment Node")
        user_message = state.get("user_message", "").strip()

        patient_record = state.get("user_info_db")
        patient_id = patient_record.get("patient_id")
        appointment = state.get("selected_appointment")
        state["current_node"] = Nodes.ACTION_APPOINTMENT_LIST
        if user_message not in self.valid_actions:
            updated_state = QAState(**{
                **state,
                "assistant_message": "Invalid action. Please try again.",
                "route": Routes.WRONG_ACTION_CHOICE,
                "phase": "action_processing"
            })
            return updated_state
        
        action = self.valid_actions[user_message]
        logger.info(f"Processing action: '{action}' for appointment: {appointment}")
        start_time = datetime.fromisoformat(appointment['starts_at'].replace('+00:00', ''))
            
        date_str = start_time.strftime('%B %d, %Y')
        time_str = start_time.strftime('%I:%M %p')

        if action == "confirm_appointment" and appointment:
            self.query_service.update_appointment_status(
                appointment_id=appointment["id"],
                new_status="confirmed"
            )
            message = f"Your appointment on {date_str} at {time_str} has been confirmed."
            updated_state = QAState(**{
                **state,
                "assistant_message": message,
                "messages": state["messages"] + [message],
                "route": Routes.CORRECT_APPOINTMENT_ACTION,
                "selected_appointment": None,
                "phase": "menu_selection"
            })
        elif action == "cancel_appointment" and appointment:
            self.query_service.update_appointment_status(
                appointment_id=appointment["id"],
                new_status="canceled_by_patient"
            )
            message = f"Your appointment on {date_str} at {time_str} has been canceled."
            updated_state = QAState(**{
                **state,
                "assistant_message": message,
                "messages": state["messages"] + [message],
                "route": Routes.CORRECT_APPOINTMENT_ACTION,
                "selected_appointment": None,
                "phase": "menu_selection"
            })
        
        elif action == "list_appointments":
            message = ""
            updated_state = QAState(**{
                **state,
                "assistant_message": message,
                "messages": state["messages"] + [message],
                "route": Routes.CORRECT_APPOINTMENT_ACTION,
                "selected_appointment": None,
                "phase": "menu_selection"
            })
            logger.info("Listed appointments for user, waiting for selection")

        return updated_state
        
