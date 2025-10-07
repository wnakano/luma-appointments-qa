from typing import Dict, Optional

from ...states.conversational_qa import QAState, StateKeys
from ...types.conversational_qa import (
	Routes, 
	Nodes,
	IntentType,
	DBAppointmentStatus,
	ConfirmationIntent
)
from ...models.conversational_qa import (
	AppointmentConfirmationResponse,
	AppointmentInfoModel
)
from ...services.conversational_qa import (
	ProcessConfirmationService,
	QueryORMService
)
from utils import Logger

logger = Logger(__name__)


class ProcessConfirmationNode:
	INTENT_STATUS_MAP: Dict[IntentType, DBAppointmentStatus] = {
		IntentType.CANCEL_APPOINTMENT: DBAppointmentStatus.CANCELED_BY_PATIENT,
		IntentType.CONFIRM_APPOINTMENT: DBAppointmentStatus.CONFIRMED,
	}
	
	CONFIRMATION_ROUTE_MAP: Dict[ConfirmationIntent, Routes] = {
		ConfirmationIntent.CONFIRM: Routes.ACTION_CONFIRMED,
		ConfirmationIntent.REJECT: Routes.ACTION_REJECTED,
	}
	
	def __init__(
		self,
		process_confirmation_service: ProcessConfirmationService,
		query_orm_service: QueryORMService
	) -> None:
		self.process_confirmation_service = process_confirmation_service
		self.query_orm_service = query_orm_service
	
	def __call__(self, state: QAState) -> QAState:
		try:
			logger.info("[NODE] ProcessConfirmationNode")
			
			appointment_record: Optional[AppointmentInfoModel] = state.get(
				StateKeys.APPOINTMENT_RECORD
			)
			user_message: str = state.get(StateKeys.USER_MESSAGE, "")
			current_intent: Optional[IntentType] = state.get(StateKeys.CURRENT_INTENT)
			
			self._validate_state(appointment_record, current_intent)
			
			appointment_id = appointment_record.appointment_id
			
			confirmation_result: AppointmentConfirmationResponse = (
				self.process_confirmation_service.run(user_message=user_message)
			)
			confirmation_intent = confirmation_result.intent
			
			logger.info(f" ... Confirmation intent: {confirmation_intent}")
			
			route = self._determine_route(confirmation_intent)
			
			if confirmation_intent == ConfirmationIntent.CONFIRM:
				self._handle_confirmation(
					appointment_id=appointment_id,
					current_intent=current_intent
				)
				state[StateKeys.APPOINTMENTS] = []
				state[StateKeys.APPOINTMENT_INFO] = None
				state[StateKeys.APPOINTMENT_RECORD] = None
				
				logger.info(" ... Cleared appointments from state after confirmation")
			elif confirmation_intent == ConfirmationIntent.REJECT:
				self._handle_rejection(appointment_id)
				state[StateKeys.APPOINTMENT_INFO] = None
			else:
				self._handle_unclear_response(confirmation_intent)
			
			state[StateKeys.CONFIRMATION_INTENT] = confirmation_result
			state[StateKeys.ROUTE] = route
			state[StateKeys.CURRENT_NODE] = Nodes.PROCESS_CONFIRMATION
			
			state[StateKeys.APPOINTMENT_RECORD] = None
			
			logger.info(f" ... Route set to: {route}")
			
			return state
			
		except Exception as e:
			logger.error(f"Error in ProcessConfirmationNode: {e}", exc_info=True)
			raise
	
	def _validate_state(
		self,
		appointment_record: Optional[AppointmentInfoModel],
		current_intent: Optional[IntentType]
	) -> None:
		if not appointment_record:
			raise ValueError("appointment_record is required but not found in state")
		
		if not appointment_record.appointment_id:
			raise ValueError("appointment_id is missing from appointment_record")
		
		if not current_intent:
			raise ValueError("current_intent is required but not found in state")
		
		if current_intent not in self.INTENT_STATUS_MAP:
			raise ValueError(
				f"Unsupported intent: {current_intent}. "
				f"Supported intents: {list(self.INTENT_STATUS_MAP.keys())}"
			)
	
	def _determine_route(self, confirmation_intent: ConfirmationIntent) -> Routes:
		return self.CONFIRMATION_ROUTE_MAP.get(
			confirmation_intent,
			Routes.ACTION_UNCLEAR
		)
	
	def _handle_confirmation(
		self,
		appointment_id: str,
		current_intent: IntentType
	) -> None:
		new_status = self.INTENT_STATUS_MAP[current_intent]
		
		logger.info(
			f" ... User confirmed action. Updating appointment {appointment_id} "
			f"to status: {new_status}"
		)
		
		result = self.query_orm_service.update_appointment_status(
			appointment_id=appointment_id,
			new_status=new_status
		)
		
		if result:
			logger.info(
				f" ... Successfully updated appointment {appointment_id} to {new_status}"
			)
		else:
			logger.warning(
				f" ... Failed to update appointment {appointment_id} status"
			)
	
	def _handle_rejection(self, appointment_id: str) -> None:
		logger.info(
			f" ... User rejected action. No changes made to appointment {appointment_id}"
		)
	
	def _handle_unclear_response(self, confirmation_intent: ConfirmationIntent) -> None:
		logger.warning(
			f" ... Unclear confirmation response: {confirmation_intent}. "
			"May need to ask for clarification."
		)