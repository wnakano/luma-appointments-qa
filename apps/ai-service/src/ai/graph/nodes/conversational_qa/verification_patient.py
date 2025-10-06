from ...states.conversational_qa import QAState, StateKeys
from ...types.conversational_qa import (
    Nodes,
    Routes, 
    IntentType
)
from ...services.conversational_qa import QueryORMService
from ...models.conversational_qa import VerificationRecordModel
from utils import Logger

logger = Logger(__name__)


class VerificationPatientNode:
    def __init__(
        self,
        query_orm_service: QueryORMService
    ) -> None:
        self.query_orm_service = query_orm_service
    
    def __call__(self, state: QAState) -> QAState:
        logger.info("[NODE] VerificationPatientNode")

        verification_info = state.get(StateKeys.USER_INFO, None)
        if verification_info:
            user_record_db = self.query_orm_service.find_user(
                user_info=verification_info
            )
            if user_record_db:
                user_record_db = user_record_db[0]
                user_record = VerificationRecordModel(
                    user_id=user_record_db['id'],
                    full_name=user_record_db['full_name'],
                    phone_number=user_record_db['phone_number'],
                    date_of_birth=user_record_db['date_of_birth'],
                )
                state[StateKeys.USER_RECORD] = user_record
                state[StateKeys.IS_VERIFIED] = True
                route = Routes.VERIFIED
            else:
                route = Routes.NOT_VERIFIED
        else:
            route = Routes.NOT_VERIFIED
        state[StateKeys.ROUTE] = route
        state[StateKeys.CURRENT_NODE] = Nodes.VERIFICATION_PATIENT

        return state

