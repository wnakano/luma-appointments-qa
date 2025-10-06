from ...states.conversational_qa import QAState
from ...types.conversational_qa import (
    Nodes,
    Routes, 
    IntentType
)
from ...services.conversational_qa import QueryORMService
from ...models.conversational_qa import VerificationRecordModel, AppointmentRecordModel
from utils import Logger

logger = Logger(__name__)


class VerificationGateNode:
    def __init__(
        self,
        query_orm_service: QueryORMService
    ) -> None:
        self.query_orm_service = query_orm_service
    
    def __call__(self, state: QAState) -> QAState:
        logger.info("[NODE] VerificationGateNode")
        
        is_verified = state.get("is_verified", False)
        appointments = state.get("appointments", [])
        appointment_record = state.get("appointment_record", None)
        user_record = state.get("user_record", None)
        
        if not all([
            is_verified,
            isinstance(user_record, VerificationRecordModel)
        ]):
            route = Routes.USER_VERIFICATION
        
        elif not all([
            len(appointments) > 0, 
            isinstance(appointment_record, AppointmentRecordModel)
        ]):
            route = Routes.APPOINTMENT_VERIFICATION

        else:
            route = Routes.VERIFIED

        state['route'] = route
        state["current_node"] = Nodes.VERIFICATION_GATE

        return state

