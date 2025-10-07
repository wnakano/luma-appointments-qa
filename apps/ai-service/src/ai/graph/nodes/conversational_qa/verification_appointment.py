from typing import Dict, List, Optional, Tuple

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
	"""
	Node responsible for verifying appointment information and matching appointments.
	
	Provides detailed diagnostic feedback when verification fails to help guide
	users to provide the correct information.
	"""
	
	MIN_REQUIRED_FIELDS = 1
	
	APPOINTMENT_ACTION_INTENTS = {
		IntentType.CONFIRM_APPOINTMENT,
		IntentType.CANCEL_APPOINTMENT,
		IntentType.APPOINTMENT_INFORMATION
	}
	
	APPOINTMENT_FIELDS = [
		"doctor_full_name",
		"clinic_name", 
		"appointment_date",
		"specialty"
	]
	
	def __init__(
		self,
		query_orm_service: QueryORMService,
		appointment_match_service: AppointmentMatchService
	) -> None:
		"""
		Initialize VerificationAppointmentNode.
		
		Args:
			query_orm_service: Service for database operations
			appointment_match_service: Service for intelligent appointment matching
		"""
		self.query_orm_service = query_orm_service
		self.appointment_match_service = appointment_match_service
	
	def __call__(self, state: QAState) -> QAState:
		""" Verify appointment information and determine appropriate route. """
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
			
			route, diagnostic_info = self._determine_route_with_diagnostics(
				current_intent=current_intent,
				appointment_info=appointment_info,
				appointment_record=appointment_record,
				appointments=appointments,
				state=state
			)
			
			if route == Routes.VERIFIED:
				logger.info(" ... Appointment verified successfully")
			else:
				if diagnostic_info:
					state[StateKeys.APPOINTMENT_DIAGNOSTICS] = diagnostic_info
					logger.info(
						f" ... Verification failed: {diagnostic_info.get('reason')} - "
						f"{diagnostic_info.get('message')}"
					)
					
					self._update_state_by_diagnostics(state, diagnostic_info)
			
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
		""" Validate that required state data is present. """
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
		""" Load appointments from database for the user. """
		logger.info(f" ... Loading appointments for patient ID: {user_record.user_id}")
		
		appointments = self.query_orm_service.find_appointments_by_patient_id(
			patient_id=user_record.user_id
		)
		
		if not appointments:
			logger.warning(" ... No appointments found for patient")
		else:
			logger.info(f" ... Loaded {len(appointments)} appointment(s)")
		
		state[StateKeys.APPOINTMENTS] = appointments
		
		return appointments
	
	def _determine_route_with_diagnostics(
		self,
		current_intent: IntentType,
		appointment_info: Optional[AppointmentInfoModel],
		appointment_record: Optional[AppointmentRecordModel],
		appointments: List[Dict],
		state: QAState
	) -> Tuple[Routes, Optional[Dict]]:
		""" Determine route with diagnostic feedback. """
		if current_intent == IntentType.LIST_APPOINTMENTS:
			return Routes.VERIFIED, None
		
		elif current_intent == IntentType.USER_INFORMATION:
			return Routes.NOT_VERIFIED, None
		
		elif current_intent in self.APPOINTMENT_ACTION_INTENTS:
			return self._verify_appointment_with_diagnostics(
				appointment_info=appointment_info,
				appointment_record=appointment_record,
				appointments=appointments,
				state=state
			)
		
		else:
			logger.warning(f"Unhandled intent: {current_intent}")
			return Routes.NOT_VERIFIED, {
				"reason": "unknown_intent",
				"message": "Unable to process your request."
			}
	
	def _verify_appointment_with_diagnostics(
		self,
		appointment_info: Optional[AppointmentInfoModel],
		appointment_record: Optional[AppointmentRecordModel],
		appointments: List[Dict],
		state: QAState
	) -> Tuple[Routes, Optional[Dict]]:
		"""Verify appointment details with comprehensive diagnostics. """
		if not appointments or len(appointments) == 0:
			logger.info(" ... No appointments available for patient")
			return Routes.NOT_VERIFIED, {
				"reason": "no_appointments",
				"missing_fields": self.APPOINTMENT_FIELDS,
				"message": (
					"You don't have any scheduled appointments. "
					"Would you like to schedule a new appointment?"
				)
			}
		
		if not appointment_info:
			logger.info(" ... No appointment info provided")
			return Routes.NOT_VERIFIED, {
				"reason": "no_info_provided",
				"missing_fields": self.APPOINTMENT_FIELDS,
				"message": (
					"Please provide details about your appointment such as "
					"the doctor's name, clinic name, appointment date, or specialty."
				)
			}
		
		if appointment_record:
			logger.info(" ... Appointment already verified")
			return Routes.VERIFIED, None
		
		incomplete_fields = self._get_incomplete_fields(appointment_info)
		if not self._has_sufficient_info(appointment_info):
			logger.warning(
				f" ... Insufficient appointment details: {len(incomplete_fields)} fields empty"
			)
			return Routes.NOT_VERIFIED, {
				"reason": "incomplete_info",
				"missing_fields": incomplete_fields,
				"message": self._generate_missing_fields_message(incomplete_fields)
			}
		
		return self._match_appointment_with_diagnostics(
			appointment_info=appointment_info,
			appointments=appointments,
			state=state
		)

	def _get_incomplete_fields(
		self,
		appointment_info: AppointmentInfoModel
	) -> List[str]:
		""" Get list of incomplete/missing appointment fields. """
		incomplete = []
		
		if not appointment_info.doctor_full_name or not appointment_info.doctor_full_name.strip():
			incomplete.append("doctor_full_name")
		
		if not appointment_info.clinic_name or not appointment_info.clinic_name.strip():
			incomplete.append("clinic_name")
		
		if not appointment_info.appointment_date or not appointment_info.appointment_date.strip():
			incomplete.append("appointment_date")
		
		if not appointment_info.specialty or not appointment_info.specialty.strip():
			incomplete.append("specialty")
		
		return incomplete
	
	def _has_sufficient_info(self, appointment_info: AppointmentInfoModel) -> bool:
		""" Check if appointment info has sufficient fields for matching. """
		fields = [
			appointment_info.doctor_full_name,
			appointment_info.clinic_name,
			appointment_info.appointment_date,
			appointment_info.specialty
		]
		
		filled_fields = [field for field in fields if field and field.strip()]
		has_enough = len(filled_fields) >= self.MIN_REQUIRED_FIELDS
		
		if not has_enough:
			logger.info(
				f" ... Only {len(filled_fields)}/{self.MIN_REQUIRED_FIELDS} "
				"required fields provided"
			)
		
		return has_enough
	
	def _generate_missing_fields_message(self, missing_fields: List[str]) -> str:
		""" Generate user-friendly message about missing fields."""
		field_labels = {
			"doctor_full_name": "doctor's name",
			"clinic_name": "clinic name",
			"appointment_date": "appointment date",
			"specialty": "doctor's specialty"
		}
		
		friendly_names = [
			field_labels.get(field, field.replace("_", " "))
			for field in missing_fields
		]
		
		if len(friendly_names) == 1:
			fields_text = friendly_names[0]
		elif len(friendly_names) == 2:
			fields_text = f"{friendly_names[0]} and {friendly_names[1]}"
		else:
			fields_text = ", ".join(friendly_names[:-1]) + f", and {friendly_names[-1]}"
		
		return f"Please provide the {fields_text} for your appointment."
	
	def _match_appointment_with_diagnostics(
		self,
		appointment_info: AppointmentInfoModel,
		appointments: List[Dict],
		state: QAState
	) -> Tuple[Routes, Optional[Dict]]:
		"""
		Attempt to match appointment with diagnostic feedback.
		
		Args:
			appointment_info: Appointment information to match
			appointments: List of user's appointments
			state: Current conversation state
			
		Returns:
			Tuple of (route, diagnostic_info)
		"""
		logger.info(" ... Attempting to match appointment")
		
		# Use matching service
		match_result: AppointmentMatchModel = self.appointment_match_service.run(
			appointments=appointments,
			appointment_info=appointment_info
		)
		
		if not match_result.match_found or not match_result.matched_appointment_id:
			logger.info(" ... No matching appointment found")
			
			diagnostic_info = self._diagnose_appointment_matching_failure(
				appointment_info=appointment_info,
				appointments=appointments,
				match_result=match_result
			)
			
			state[StateKeys.APPOINTMENT_RECORD] = None
			return Routes.NOT_VERIFIED, diagnostic_info
		
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
			return Routes.NOT_VERIFIED, {
				"reason": "match_not_found_in_list",
				"message": "Unable to locate the matched appointment. Please try again."
			}
		
		appointment_record = self._create_appointment_record(matched_appointment)
		state[StateKeys.APPOINTMENT_RECORD] = appointment_record
		
		logger.info(
			f" ... Successfully matched appointment ID: "
			f"{match_result.matched_appointment_id}"
		)
		
		return Routes.VERIFIED, None
	
	def _diagnose_appointment_matching_failure(
		self,
		appointment_info: AppointmentInfoModel,
		appointments: List[Dict],
		match_result: AppointmentMatchModel
	) -> Dict:
		logger.info(" ... Running appointment matching diagnostics")
		
		provided_fields = []
		if appointment_info.doctor_full_name:
			provided_fields.append("doctor_full_name")
		if appointment_info.clinic_name:
			provided_fields.append("clinic_name")
		if appointment_info.appointment_date:
			provided_fields.append("appointment_date")
		if appointment_info.specialty:
			provided_fields.append("specialty")
		
		logger.info(f" ... Provided fields: {provided_fields}")
		
		partial_matches = {}
		best_match_appointment = None
		
		for appt in appointments:
			matches = []
			
			if appointment_info.doctor_full_name:
				doctor_in_db = appt.get("provider", {}).get("full_name", "").lower()
				if appointment_info.doctor_full_name.lower() in doctor_in_db or \
				doctor_in_db in appointment_info.doctor_full_name.lower():
					matches.append("doctor_full_name")
			
			if appointment_info.clinic_name:
				clinic_in_db = appt.get("clinic", {}).get("name", "").lower()
				if appointment_info.clinic_name.lower() in clinic_in_db or \
				clinic_in_db in appointment_info.clinic_name.lower():
					matches.append("clinic_name")
			
			if appointment_info.appointment_date:
				date_in_db = appt.get("starts_at", "").lower()
				if appointment_info.appointment_date.lower() in date_in_db or \
				date_in_db in appointment_info.appointment_date.lower():
					matches.append("appointment_date")
			
			if appointment_info.specialty:
				specialty_in_db = appt.get("provider", {}).get("specialty", "").lower()
				if appointment_info.specialty.lower() in specialty_in_db or \
				specialty_in_db in appointment_info.specialty.lower():
					matches.append("specialty")
			
			if matches:
				appt_id = appt.get("id")
				partial_matches[appt_id] = {
					"matching_fields": matches,
					"match_count": len(matches),
					"appointment": appt
				}
		
		logger.info(f" ... Found {len(partial_matches)} partial match(es)")
		
		existing_appointments_summary = self._format_appointments_summary(appointments)
		
		if not partial_matches:
			return {
				"reason": "no_matches",
				"likely_incorrect": provided_fields,
				"possibly_correct": [],
				"existing_appointments": appointments,
				"existing_appointments_summary": existing_appointments_summary,
				"message": (
					f"I couldn't find any appointments matching the information you provided. "
					f"You have {len(appointments)} scheduled appointment(s). "
					f"Please verify the details or try describing your appointment differently."
				)
			}
		
		best_match = max(partial_matches.values(), key=lambda x: x["match_count"])
		best_matching_fields = best_match["matching_fields"]
		best_match_count = best_match["match_count"]
		best_match_appointment = best_match["appointment"]

		likely_incorrect = [
			field for field in provided_fields 
			if field not in best_matching_fields
		]
		
		if best_match_count == len(provided_fields) - 1:
			field_labels = {
				"doctor_full_name": "doctor's name",
				"clinic_name": "clinic name",
				"appointment_date": "appointment date",
				"specialty": "specialty"
			}
			incorrect_label = field_labels.get(
				likely_incorrect[0], 
				likely_incorrect[0]
			)
			
			closest_appointment_info = self._extract_appointment_info(best_match_appointment)
			
			return {
				"reason": "single_field_mismatch",
				"likely_incorrect": likely_incorrect,
				"possibly_correct": best_matching_fields,
				"closest_match": closest_appointment_info,
				"existing_appointments": appointments,
				"existing_appointments_summary": existing_appointments_summary,
				"message": (
					f"I found an appointment matching most of your information, "
					f"but the {incorrect_label} doesn't quite match. "
					f"Please verify the {incorrect_label}."
				)
			}
		
		elif best_match_count >= 1:
			closest_appointment_info = self._extract_appointment_info(best_match_appointment)
			
			return {
				"reason": "partial_match",
				"likely_incorrect": likely_incorrect,
				"possibly_correct": best_matching_fields,
				"closest_match": closest_appointment_info,
				"existing_appointments": appointments,
				"existing_appointments_summary": existing_appointments_summary,
				"message": (
					f"I found appointments matching some of your information. "
					f"Please double-check all the details you provided."
				)
			}
		
		else:
			return {
				"reason": "no_complete_match",
				"likely_incorrect": [],
				"possibly_correct": [],
				"existing_appointments": appointments,
				"existing_appointments_summary": existing_appointments_summary,
				"message": match_result.reasoning or "Unable to match your appointment."
			}

	def _extract_appointment_info(self, appointment: Dict) -> Dict[str, str]:
		return {
			"doctor_name": appointment.get("provider", {}).get("full_name", "Unknown"),
			"clinic_name": appointment.get("clinic", {}).get("name", "Unknown"),
			"appointment_date": appointment.get("starts_at", "Unknown"),
			"specialty": appointment.get("provider", {}).get("specialty", "Unknown"),
			"status": appointment.get("status", "Unknown")
		}

	def _format_appointments_summary(self, appointments: List[Dict]) -> str:
		if not appointments:
			return "No appointments scheduled."
		
		summaries = []
		for idx, appt in enumerate(appointments, 1):
			doctor = appt.get("provider", {}).get("full_name", "Unknown Doctor")
			clinic = appt.get("clinic", {}).get("name", "Unknown Clinic")
			date = appt.get("starts_at", "Unknown Date")
			specialty = appt.get("provider", {}).get("specialty", "")
			
			if specialty:
				summary = f"{idx}. {doctor} ({specialty}) at {clinic} on {date}"
			else:
				summary = f"{idx}. {doctor} at {clinic} on {date}"
			
			summaries.append(summary)
		
		return "\n".join(summaries)
	
	def _find_appointment_by_id(
		self,
		appointments: List[Dict],
		appointment_id: str
	) -> Optional[Dict]:
		""" Find appointment by ID from appointments list."""
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
		""" Create AppointmentRecordModel from appointment dictionary."""
		return AppointmentRecordModel(
			appointment_id=str(appointment.get("id")),
			doctor_full_name=appointment.get("provider", {}).get("full_name", ""),
			clinic_name=appointment.get("clinic", {}).get("name", ""),
			appointment_date=appointment.get("starts_at", ""),
			specialty=appointment.get("provider", {}).get("specialty", "")
		)

	def _update_state_by_diagnostics(
		self,
		state: QAState,
		diagnostic_info: Dict
	) -> None:
		"""Update state by clearing fields identified as likely incorrect."""
		if not diagnostic_info:
			logger.debug(" ... No diagnostic info to process")
			return
		
		reason = diagnostic_info.get("reason")
		likely_incorrect = diagnostic_info.get("likely_incorrect", [])
		
		# if reason in ["single_field_mismatch", "partial_match"] and likely_incorrect:
		if likely_incorrect:
			logger.info(f" ... Clearing incorrect appointment fields: {likely_incorrect}")
			self._clear_appointment_fields(state, likely_incorrect)
		else:
			logger.debug(f" ... Not clearing fields (reason: {reason})")
	
	def _clear_appointment_fields(
		self,
		state: QAState,
		fields_to_clear: List[str]
	) -> None:
		""" Clear specific fields from appointment_info in state. """
		appointment_info: Optional[AppointmentInfoModel] = state.get(
			StateKeys.APPOINTMENT_INFO
		)
		
		if not appointment_info:
			logger.warning(" ... No appointment_info in state to update")
			return
		
		updated_data = appointment_info.model_dump()
		
		cleared_count = 0
		for field in fields_to_clear:
			if field in updated_data:
				logger.debug(f" ... Clearing field: {field}")
				updated_data[field] = None
				cleared_count += 1
			else:
				logger.warning(f" ... Field '{field}' not found in appointment_info")
		
		state[StateKeys.APPOINTMENT_INFO] = AppointmentInfoModel(**updated_data)
		
		logger.info(f" ... Cleared {cleared_count} field(s) from appointment_info")