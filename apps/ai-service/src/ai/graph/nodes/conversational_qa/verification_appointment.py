from typing import Dict, List, Optional

from ...states.conversational_qa import QAState, StateKeys
from ...types.conversational_qa import (
	Routes, 
	Nodes,
	IntentType
)
from ...services.conversational_qa import QueryORMService, AppointmentMatchService
from ...models.conversational_qa import (
	VerificationRecordModel, 
	AppointmentRecordModel,
	AppointmentInfoModel,
	AppointmentMatchModel
)
from utils import Logger

logger = Logger(__name__)


class VerificationAppointmentNode:

	MIN_REQUIRED_FIELDS = 1
	APPOINTMENT_ACTION_INTENTS = {
		IntentType.CONFIRM_APPOINTMENT,
		IntentType.CANCEL_APPOINTMENT,
		IntentType.APPOINTMENT_INFORMATION
	}
	
	def __init__(
		self,
		query_orm_service: QueryORMService,
		appointment_match_service: AppointmentMatchService
	) -> None:
		self.query_orm_service = query_orm_service
		self.appointment_match_service = appointment_match_service
	
	def __call__(self, state: QAState) -> QAState:

		try:
			logger.info("[NODE] VerificationAppointmentNode")
			
			appointment_info: Optional[AppointmentInfoModel] = state.get(
				StateKeys.APPOINTMENT_INFO
			)
			appointment_record: Optional[AppointmentRecordModel] = state.get(
				StateKeys.APPOINTMENT_RECORD
			)
			appointments: List[Dict] = state.get(StateKeys.APPOINTMENTS, [])
			user_record: Optional[VerificationRecordModel] = state.get(
				StateKeys.USER_RECORD
			)
			current_intent: Optional[IntentType] = state.get(StateKeys.CURRENT_INTENT)

			self._validate_state(user_record, current_intent)
			
			if not appointments:
				appointments = self._load_appointments(state, user_record)
			
			logger.info(
				f" ... Current intent: {current_intent}, "
				f"Appointments count: {len(appointments)}"
			)
			
			route = self._determine_route(
				current_intent=current_intent,
				appointment_info=appointment_info,
				appointment_record=appointment_record,
				appointments=appointments,
				state=state
			)
			
			state[StateKeys.CURRENT_NODE] = Nodes.VERIFICATION_APPOINTMENT
			state[StateKeys.ROUTE] = route
			
			logger.info(f" ... Route set to: {route}")
			
			return state
			
		except Exception as e:
			logger.error(f"Error in VerificationAppointmentNode: {e}", exc_info=True)
			raise
	
	def _validate_state(
		self,
		user_record: Optional[VerificationRecordModel],
		current_intent: Optional[IntentType]
	) -> None:
		if not user_record:
			raise ValueError("user_record is required but not found in state")
		
		if not user_record.user_id:
			raise ValueError("user_id is missing from user_record")
		
		if not current_intent:
			raise ValueError("current_intent is required but not found in state")
	
	def _load_appointments(
		self,
		state: QAState,
		user_record: VerificationRecordModel
	) -> List[Dict]:

		logger.info(f" ... Loading appointments for patient ID: {user_record.user_id}")
		
		appointments = self.query_orm_service.find_appointments_by_patient_id(
			patient_id=user_record.user_id
		)
		
		logger.info(f" ... Loaded {len(appointments)} appointments")
		state[StateKeys.APPOINTMENTS] = appointments
		
		return appointments
	
	def _determine_route(
		self,
		current_intent: IntentType,
		appointment_info: Optional[AppointmentInfoModel],
		appointment_record: Optional[AppointmentRecordModel],
		appointments: List[Dict],
		state: QAState
	) -> Routes:
		if current_intent == IntentType.LIST_APPOINTMENTS:
			return Routes.VERIFIED
		elif current_intent == IntentType.USER_INFORMATION:
			return Routes.NOT_VERIFIED
		elif current_intent in self.APPOINTMENT_ACTION_INTENTS:
			return self._verify_appointment_details(
				appointment_info=appointment_info,
				appointment_record=appointment_record,
				appointments=appointments,
				state=state
			)
		else:
			logger.warning(f"Unhandled intent in VerificationAppointmentNode: {current_intent}")
			return Routes.NOT_VERIFIED
	
	def _verify_appointment_details(
		self,
		appointment_info: Optional[AppointmentInfoModel],
		appointment_record: Optional[AppointmentRecordModel],
		appointments: List[Dict],
		state: QAState
	) -> Routes:
		if not appointment_info:
			logger.info(" ... No appointment info provided")
			return Routes.NOT_VERIFIED
		if appointment_record:
			logger.info(" ... Appointment already verified")
			return Routes.VERIFIED
		if not self._has_sufficient_info(appointment_info):
			logger.warning(" ... Insufficient appointment details for matching")
			return Routes.NOT_VERIFIED
		return self._match_appointment(
			appointment_info=appointment_info,
			appointments=appointments,
			state=state
		)
	
	def _has_sufficient_info(self, appointment_info: AppointmentInfoModel) -> bool:
		fields = [
			appointment_info.doctor_full_name,
			appointment_info.clinic_name,
			appointment_info.appointment_date,
			appointment_info.specialty
		]
		
		filled_fields = [field for field in fields if field]
		
		has_enough = len(filled_fields) >= self.MIN_REQUIRED_FIELDS
		
		if not has_enough:
			logger.info(
				f" ... Only {len(filled_fields)}/{self.MIN_REQUIRED_FIELDS} "
				"required fields provided"
			)
		
		return has_enough
	
	def _match_appointment(
		self,
		appointment_info: AppointmentInfoModel,
		appointments: List[Dict],
		state: QAState
	) -> Routes:
		logger.info(" ... Attempting to match appointment")
	
		match_result: AppointmentMatchModel = self.appointment_match_service.run(
			appointments=appointments,
			appointment_info=appointment_info
		)
		
		if not match_result.match_found or not match_result.matched_appointment_id:
			logger.info(" ... No matching appointment found")
			state[StateKeys.APPOINTMENT_RECORD] = None
			return Routes.NOT_VERIFIED

		matched_appointment = self._find_appointment_by_id(
			appointments=appointments,
			appointment_id=match_result.matched_appointment_id
		)
		
		if not matched_appointment:
			logger.error(
				f" ... Matched appointment ID {match_result.matched_appointment_id} "
				"not found in appointments list"
			)
			state[StateKeys.APPOINTMENT_RECORD] = None
			return Routes.NOT_VERIFIED
		
		appointment_record = self._create_appointment_record(matched_appointment)
		state[StateKeys.APPOINTMENT_RECORD] = appointment_record
		
		logger.info(
			f" ... Successfully matched appointment ID: "
			f"{match_result.matched_appointment_id}"
		)
		
		return Routes.VERIFIED
	
	def _find_appointment_by_id(
		self,
		appointments: List[Dict],
		appointment_id: str
	) -> Optional[Dict]:
		matching_appointments = [
			appt for appt in appointments 
			if str(appt.get("id")) == str(appointment_id)
		]
		
		if not matching_appointments:
			return None
		
		if len(matching_appointments) > 1:
			logger.warning(
				f"Multiple appointments found with ID {appointment_id}, using first"
			)
		
		return matching_appointments[0]
	
	def _create_appointment_record(
		self,
		appointment: Dict
	) -> AppointmentRecordModel:

		return AppointmentRecordModel(
			appointment_id=str(appointment.get("id")),
			doctor_full_name=appointment.get("provider", {}).get("full_name", ""),
			clinic_name=appointment.get("clinic", {}).get("name", ""),
			appointment_date=appointment.get("starts_at", ""),
			specialty=appointment.get("provider", {}).get("specialty", "")
		)