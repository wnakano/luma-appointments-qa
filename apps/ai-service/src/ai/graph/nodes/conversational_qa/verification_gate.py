from typing import List, Optional

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
	def __init__(self, query_orm_service: QueryORMService) -> None:
		self.query_orm_service = query_orm_service
	
	def __call__(self, state: QAState) -> QAState:

		try:
			logger.info("[NODE] VerificationGateNode")
			
			is_verified = state.get(StateKeys.IS_VERIFIED, False)
			user_record: Optional[VerificationRecordModel] = state.get(
				StateKeys.USER_RECORD
			)
			appointments: List = state.get(StateKeys.APPOINTMENTS, [])
			appointment_record: Optional[AppointmentRecordModel] = state.get(
				StateKeys.APPOINTMENT_RECORD
			)

			route = self._determine_verification_route(
				is_verified=is_verified,
				user_record=user_record,
				appointments=appointments,
				appointment_record=appointment_record
			)

			state[StateKeys.ROUTE] = route
			state[StateKeys.CURRENT_NODE] = Nodes.VERIFICATION_GATE
			
			logger.info(f" ... Verification route set to: {route}")
			
			return state
			
		except Exception as e:
			logger.error(f"Error in VerificationGateNode: {e}", exc_info=True)
			raise
	
	def _determine_verification_route(
		self,
		is_verified: bool,
		user_record: Optional[VerificationRecordModel],
		appointments: List,
		appointment_record: Optional[AppointmentRecordModel]
	) -> Routes:
		user_is_verified = self._is_user_verified(is_verified, user_record)
		
		if not user_is_verified:
			logger.info(" ... User not verified, routing to user verification")
			return Routes.USER_VERIFICATION
		appointment_is_verified = self._is_appointment_verified(
			appointments, appointment_record
		)
		
		if not appointment_is_verified:
			logger.info(" ... User verified but appointment not verified, routing to appointment verification")
			return Routes.APPOINTMENT_VERIFICATION
		logger.info(" ... Both user and appointment verified")
		return Routes.VERIFIED
	
	def _is_user_verified(
		self,
		is_verified: bool,
		user_record: Optional[VerificationRecordModel]
	) -> bool:
		has_valid_record = isinstance(user_record, VerificationRecordModel)
		verified = is_verified and has_valid_record
		
		if not verified:
			if not is_verified:
				logger.debug(" ... is_verified flag is False")
			if not has_valid_record:
				logger.debug(" ... user_record is missing or invalid")
		
		return verified
	
	def _is_appointment_verified(
		self,
		appointments: List,
		appointment_record: Optional[AppointmentRecordModel]
	) -> bool:
		has_appointments = len(appointments) > 0
		has_matched_appointment = isinstance(appointment_record, AppointmentRecordModel)
		
		verified = has_appointments and has_matched_appointment
		
		if not verified:
			if not has_appointments:
				logger.debug(" ... No appointments found")
			if not has_matched_appointment:
				logger.debug(" ... No appointment record matched")
		
		return verified