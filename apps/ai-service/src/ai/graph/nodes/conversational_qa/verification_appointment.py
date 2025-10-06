from ...states.conversational_qa import QAState, StateKeys
from ...types.conversational_qa import (
	Routes, 
	Nodes,
	IntentType
)
from ...services.conversational_qa import QueryORMService, AppointmentMatchService
from ...models.conversational_qa import VerificationRecordModel, AppointmentRecordModel
from utils import Logger

logger = Logger(__name__)


class VerificationAppointmentNode:
	def __init__(
		self,
		query_orm_service: QueryORMService,
		appointment_match_service: AppointmentMatchService
	) -> None:
		self.query_orm_service = query_orm_service
		self.appointment_match_service = appointment_match_service
	
	def __call__(self, state: QAState) -> QAState:
		logger.info("[NODE] VerificationAppointmentNode")

		appointment_info = state.get(StateKeys.APPOINTMENT_INFO, None)
		appointment_record = state.get(StateKeys.APPOINTMENT_RECORD, None)
		appointments = state.get(StateKeys.APPOINTMENTS, [])
		user_record = state.get(StateKeys.USER_RECORD, None)
		current_intent = state.get(StateKeys.CURRENT_INTENT)


		logger.info(f"appointments = {appointments}")
		logger.info(f"user_record = {user_record}")
		logger.info(f"appointment_info = {appointment_info}")
		logger.info(f"appointment_record = {appointment_record}")
		
		if not appointments:
			appointments = self.query_orm_service.find_appointments_by_patient_id(
				patient_id=user_record.user_id
			)
			logger.info(f"appointments = {appointments}")
			state[StateKeys.APPOINTMENTS] = appointments
		
		logger.info(f"current_intent = {current_intent}")
		if current_intent == IntentType.LIST_APPOINTMENTS:
			route = Routes.VERIFIED
		elif current_intent == IntentType.USER_INFORMATION:
			route = Routes.NOT_VERIFIED
		# elif current_intent == IntentType.APPOINTMENT_INFORMATION:


		elif current_intent in [
			IntentType.CONFIRM_APPOINTMENT, 
			IntentType.CANCEL_APPOINTMENT, 
			IntentType.APPOINTMENT_INFORMATION
		]:
			if appointment_info:
				doctor_full_name = appointment_info.doctor_full_name
				clinic_name = appointment_info.clinic_name
				appointment_date = appointment_info.appointment_date
				specialty = appointment_info.specialty
				if not appointment_record:
					if not len(list(filter(lambda data: data, 
						[doctor_full_name, clinic_name, appointment_date, specialty]))) >= 2:
						logger.warning(f"Not enough data to query appointment: {appointment_info}")
						route = Routes.NOT_VERIFIED
					else:
						logger.info(f"Quering appointment: {appointment_info}")
						result_appointment_match = self.appointment_match_service.run(
							appointments=appointments,
							appointment_info=appointment_info
						)
						logger.info(f"Appointment found: {result_appointment_match}")
						matched_appointment_id = result_appointment_match.matched_appointment_id
						match_found = result_appointment_match.match_found
						appointments_ = [appt for appt in appointments if str(appt["id"]) == matched_appointment_id]
						appointment_ = appointments_[0]
						logger.info(f"appointment_ = {appointment_}")
						if match_found and matched_appointment_id:
							appointment_record = AppointmentRecordModel(
								appointment_id=matched_appointment_id,
								doctor_full_name=appointment_["provider"]["full_name"],
								clinic_name=appointment_["clinic"]["name"],
								appointment_date=appointment_["starts_at"],
								specialty=appointment_["provider"]["specialty"]
							)
							state[StateKeys.APPOINTMENT_RECORD] = appointment_record
							route = Routes.VERIFIED
						else:
							state[StateKeys.APPOINTMENT_RECORD] = None
							route = Routes.NOT_VERIFIED
			else:
				route = Routes.NOT_VERIFIED



		state[StateKeys.CURRENT_NODE] = Nodes.VERIFICATION_APPOINTMENT
		state[StateKeys.ROUTE] = route

		return state

