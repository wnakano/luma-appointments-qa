from ...states.conversational_qa import QAState, StateKeys
from ...types.conversational_qa import (
	Routes, 
	Nodes,
	IntentType,
	DBAppointmentStatus,
	ConfirmationIntent
)
from ...models.conversational_qa import AppointmentConfirmationResponse
from ...services.conversational_qa import (
    ProcessConfirmationService,
    QueryORMService
)
from utils import Logger

logger = Logger(__name__)


class ProcessConfirmationNode:
	def __init__(
		self,
		process_confirmation_service: ProcessConfirmationService,
		query_orm_service:QueryORMService
	) -> None:
		self.process_confirmation_service = process_confirmation_service
		self.query_orm_service = query_orm_service
	
	def __call__(self, state: QAState) -> QAState:
		logger.info("[NODE] ProcessConfirmationNode")
		appointment_record = state.get(StateKeys.APPOINTMENT_INFO)
		appointment_id = appointment_record.appointment_id
		user_message = state.get(StateKeys.USER_MESSAGE)
		current_intent = state.get(StateKeys.CURRENT_INTENT)
		messages = state.get(StateKeys.MESSAGES, [])
		
		confirmation_result = self.process_confirmation_service.run(
			user_message=user_message
		)
		confirmation_intent = confirmation_result.intent
		logger.info(f"Confirmation Intent: {confirmation_intent}")
		if confirmation_intent == ConfirmationIntent.CONFIRM:
			route = Routes.ACTION_CONFIRMED
			if current_intent == IntentType.CANCEL_APPOINTMENT:
				new_status = DBAppointmentStatus.CANCELED_BY_PATIENT
			elif current_intent == IntentType.CONFIRM_APPOINTMENT:
				new_status = DBAppointmentStatus.CONFIRMED
			_ = self.query_orm_service.update_appointment_status(
				appointment_id=appointment_id,
				new_status=new_status
			)
			logger.info(f"Appointment: {appointment_id} -> {new_status}")
			state[StateKeys.APPOINTMENTS] = []
			
		elif confirmation_intent == ConfirmationIntent.REJECT:
			route = Routes.ACTION_REJECTED
			state[StateKeys.APPOINTMENTS] = []
		else:
			route = Routes.ACTION_UNCLEAR

		state[StateKeys.CONFIRMATION_INTENT] = confirmation_result
		state[StateKeys.ROUTE] = route

		state[StateKeys.CURRENT_NODE] = Nodes.PROCESS_CONFIRMATION

		return state

