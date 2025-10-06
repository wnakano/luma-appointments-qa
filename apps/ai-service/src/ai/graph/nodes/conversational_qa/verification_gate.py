from ...states.conversational_qa import QAState, StateKeys
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

        is_verified = state.get(StateKeys.IS_VERIFIED, False)
        appointments = state.get(StateKeys.APPOINTMENTS, [])
        appointment_record = state.get(StateKeys.APPOINTMENT_RECORD, None)
        user_record = state.get(StateKeys.USER_RECORD, None)

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

        state[StateKeys.ROUTE] = route
        state[StateKeys.CURRENT_NODE] = Nodes.VERIFICATION_GATE

        return state

