

from ...states.conversational_qa import QAState
from ...services.conversational_qa import IntentService
from ...types.conversational_qa import (
    Nodes,
    Routes, 
    IntentType
)
from ...models.conversational_qa import ConversationIntentModel
from utils import Logger

logger = Logger(__name__)


class ConversationManagerNode:
    def __init__(
        self,
        intent_service: IntentService
    ) -> None:
        self.intent_service = intent_service
    
    def __call__(self, state: QAState):
        logger.info("[NODE] ConversationManagerNode")
        is_verified = state.get("is_verified", False)

        intent_result: ConversationIntentModel = self.intent_service.run(
            state=state
        )
        
        user_intent = intent_result.user_intent.intent_type
        state["current_intent"] = user_intent.value
        
        if user_intent == IntentType.GENERAL_QA:
            route = Routes.ACTION_QA
        
        elif user_intent in [
            IntentType.LIST_APPOINTMENTS, 
            IntentType.CONFIRM_APPOINTMENT,
            IntentType.CANCEL_APPOINTMENT
            ]:
            route = Routes.ACTION_APPPOINTMENT
            if not is_verified and hasattr(intent_result, "verification_info"):
                verification_info = intent_result.verification_info
                full_name = verification_info.full_name
                phone_number = verification_info.phone_number
                date_of_birth = verification_info.date_of_birth

                state['user_info'] = verification_info
                state['full_name'] = full_name
                state['phone_number'] = phone_number
                state['date_of_birth'] = date_of_birth

            if hasattr(intent_result, "appointment_info"):
                appointment_info = intent_result.appointment_info
                state["appointment_info"] = appointment_info
            

        state["route"] = route
        state["current_node"] = Nodes.CONVERSATION_MANAGER
        
        logger.info(f"Route set to: {state['route']}")
        
        return state