from ...states.conversational_qa import QAState, StateKeys
from ...types.conversational_qa import (
    Nodes,
    DBAppointmentStatus
)
from ...services.conversational_qa import QueryORMService
from utils import Logger


logger = Logger(__name__)


class CancelAppointmentNode:
    def __init__(
        self,
        query_orm_service: QueryORMService
    ) -> None:
        self.query_orm_service = query_orm_service
    
    def __call__(self, state: QAState) -> QAState:
        logger.info("[NODE] CancelAppointmentNode")
        appointment_record = state.get(StateKeys.APPOINTMENT_INFO)
        appointment_id = appointment_record.appointment_id
        _ = self.query_orm_service.update_appointment_status(
            appointment_id=appointment_id,
            new_status=DBAppointmentStatus.CONFIRMED
        )

        state[StateKeys.CURRENT_NODE] = Nodes.CANCEL_APPOINTMENTS
        return state