from typing import Dict, List, Optional, Tuple

from ...states.conversational_qa import QAState, StateKeys
from ...types.conversational_qa import (
	Nodes,
	Routes, 
	IntentType
)
from ...services.conversational_qa import QueryORMService
from ...models.conversational_qa import VerificationRecordModel, VerificationInfoModel
from utils import Logger

logger = Logger(__name__)


class VerificationPatientNode:
	def __init__(self, query_orm_service: QueryORMService) -> None:
		self.query_orm_service = query_orm_service
	
	def __call__(self, state: QAState) -> QAState:

		try:
			logger.info("[NODE] VerificationPatientNode")
			
			verification_info: Optional[VerificationInfoModel] = state.get(
				StateKeys.USER_INFO
			)
			
			route, user_record, diagnostic_info = self._verify_user(verification_info)

			if route == Routes.VERIFIED:
				state[StateKeys.USER_RECORD] = user_record
				state[StateKeys.IS_VERIFIED] = True
				logger.info(f" ... User verified: {user_record.full_name}")
			else:
				self._update_state_by_diagnostics(
					state=state, 
					diagnostic_info=diagnostic_info
				)
				state[StateKeys.USER_RECORD] = None
				state[StateKeys.IS_VERIFIED] = False
				state[StateKeys.VERIFICATION_DIAGNOSTICS] = diagnostic_info
				logger.info(" ... User verification failed")
			
			state[StateKeys.ROUTE] = route
			state[StateKeys.CURRENT_NODE] = Nodes.VERIFICATION_PATIENT
			
			return state
			
		except Exception as e:
			logger.error(f"Error in VerificationPatientNode: {e}", exc_info=True)
			raise
	
	def _verify_user(
		self,
		verification_info: Optional[VerificationInfoModel]
	) -> Tuple[Routes, Optional[VerificationRecordModel], Optional[Dict]]:

		if not verification_info:
			logger.info(" ... No verification info provided")
			return Routes.NOT_VERIFIED, None, {
				"reason": "no_info_provided",
				"missing_fields": ["full_name", "phone_number", "date_of_birth"],
				"message": "Please provide your full name, phone number, and date of birth."
			}
		
		incomplete_fields = self._get_incomplete_fields(verification_info)
		if incomplete_fields:
			logger.info(f" ... Incomplete verification info: {incomplete_fields}")
			return Routes.NOT_VERIFIED, None, {
				"reason": "incomplete_info",
				"missing_fields": incomplete_fields,
				"message": f"Please provide your {self._format_field_list(incomplete_fields)}."
			}
		
		logger.info(" ... Querying database for user")
		user_records: List[Dict] = self.query_orm_service.find_user(
			user_info=verification_info
		)
		
		if not user_records or len(user_records) == 0:
			logger.info(" ... No matching user found in database")
			diagnostic_info = self._diagnose_verification_failure(verification_info)
			return Routes.NOT_VERIFIED, None, diagnostic_info
		
		if len(user_records) > 1:
			logger.warning(
				f" ... Multiple users found ({len(user_records)}), using first match"
			)
		
		user_data = user_records[0]
		user_record = self._create_user_record(user_data)
		
		logger.info(f" ... User found: ID={user_record.user_id}")
		
		return Routes.VERIFIED, user_record, {
			"reason": "verified",
			"message": "User verified successfully"
		}
	
	def _get_incomplete_fields(
		self, 
		verification_info: VerificationInfoModel
	) -> List[str]:
		incomplete = []
		
		if not verification_info.full_name or not verification_info.full_name.strip():
			incomplete.append("full_name")
		
		if not verification_info.phone_number or not verification_info.phone_number.strip():
			incomplete.append("phone_number")
		
		if not verification_info.date_of_birth or not verification_info.date_of_birth.strip():
			incomplete.append("date_of_birth")
		
		return incomplete
	
	def _diagnose_verification_failure(
		self,
		verification_info: VerificationInfoModel
	) -> Dict:
		logger.info(" ... Running verification diagnostics")
		
		matches_by_field = {}
		
		if verification_info.phone_number:
			phone_matches = self.query_orm_service.find_user(
				user_info=VerificationInfoModel(
					phone_number=verification_info.phone_number,
					full_name=None,
					date_of_birth=None
				),
				allow_partial=True
			)
			matches_by_field["phone_number"] = len(phone_matches) if phone_matches else 0
		
		if verification_info.full_name:
			name_matches = self.query_orm_service.find_user(
				user_info=VerificationInfoModel(
					full_name=verification_info.full_name,
					phone_number=None,
					date_of_birth=None
				),
				allow_partial=True
			)
			matches_by_field["full_name"] = len(name_matches) if name_matches else 0
		
		if verification_info.date_of_birth:
			dob_matches = self.query_orm_service.find_user(
				user_info=VerificationInfoModel(
					date_of_birth=verification_info.date_of_birth,
					full_name=None,
					phone_number=None
				),
				allow_partial=True
			)
			matches_by_field["date_of_birth"] = len(dob_matches) if dob_matches else 0
		
		logger.info(f" ... Diagnostic results: {matches_by_field}")
		
		likely_incorrect = []
		possibly_correct = []
		
		for field, count in matches_by_field.items():
			if count == 0:
				likely_incorrect.append(field)
			elif count > 0:
				possibly_correct.append(field)
		
		if len(likely_incorrect) == 3:
			return {
				"reason": "user_not_found",
				"likely_incorrect": likely_incorrect,
				"possibly_correct": possibly_correct,
				"message": (
					"We couldn't find a user with that information in our system. "
					"Please verify your full name, phone number, and date of birth. "
					"If you're a new patient, you may need to register first."
				)
			}
		
		elif len(likely_incorrect) == 2:
			correct_field = possibly_correct[0] if possibly_correct else "unknown"
			return {
				"reason": "multiple_fields_incorrect",
				"likely_incorrect": likely_incorrect,
				"possibly_correct": possibly_correct,
				"message": (
					f"We found a record matching your {self._field_to_friendly_name(correct_field)}, "
					f"but the {self._format_field_list(likely_incorrect)} don't match. "
					f"Please verify your {self._format_field_list(likely_incorrect)}."
				)
			}
		
		elif len(likely_incorrect) == 1:
			incorrect_field = likely_incorrect[0]
			return {
				"reason": "single_field_incorrect",
				"likely_incorrect": likely_incorrect,
				"possibly_correct": possibly_correct,
				"message": (
					f"We found records matching some of your information, "
					f"but the {self._field_to_friendly_name(incorrect_field)} doesn't match. "
					f"Please verify your {self._field_to_friendly_name(incorrect_field)}."
				)
			}
		
		else:
			return {
				"reason": "no_complete_match",
				"likely_incorrect": [],
				"possibly_correct": possibly_correct,
				"message": (
					"We found partial matches for your information, but no complete match. "
					"Please double-check all fields, especially date of birth format (MM/DD/YYYY)."
				)
			}
	
	def _update_state_by_diagnostics(
		self,
		state: QAState,
		diagnostic_info: Dict
	) -> None:
		"""Update state based on diagnostic info to clear likely incorrect fields."""
		if not diagnostic_info:
			return

		likely_incorrect = diagnostic_info.get("likely_incorrect", [])
		if likely_incorrect:
			user_info = state.get(StateKeys.USER_INFO)
			updated_data = user_info.model_dump()
			for field in likely_incorrect:
				if field in updated_data:
					logger.debug(f" ... Clearing field: {field}")
					updated_data[field] = None
				else:
					logger.warning(f" ... Field '{field}' not found in user_info")
			
			state[StateKeys.USER_INFO] = VerificationInfoModel(**updated_data)
			
			logger.info(
				f" ... Updated user_info with {len(likely_incorrect)} field(s) cleared"
			)

	def _field_to_friendly_name(self, field: str) -> str:
		"""Convert field name to user-friendly name."""
		field_names = {
			"full_name": "full name",
			"phone_number": "phone number",
			"date_of_birth": "date of birth"
		}
		return field_names.get(field, field)
	
	def _format_field_list(self, fields: List[str]) -> str:
		"""Format list of fields into readable text."""
		friendly_names = [self._field_to_friendly_name(f) for f in fields]
		
		if len(friendly_names) == 0:
			return ""
		elif len(friendly_names) == 1:
			return friendly_names[0]
		elif len(friendly_names) == 2:
			return f"{friendly_names[0]} and {friendly_names[1]}"
		else:
			return ", ".join(friendly_names[:-1]) + f", and {friendly_names[-1]}"
		
	def _create_user_record(self, user_data: Dict) -> VerificationRecordModel:
		required_fields = ['id', 'full_name', 'phone_number', 'date_of_birth']
		missing_fields = [
			field for field in required_fields 
			if field not in user_data or user_data.get(field) is None
		]
		
		if missing_fields:
			raise ValueError(
				f"Missing required fields in user data: {missing_fields}"
			)
		
		# Create and return user record
		return VerificationRecordModel(
			user_id=str(user_data['id']),
			full_name=user_data['full_name'],
			phone_number=user_data['phone_number'],
			date_of_birth=user_data['date_of_birth']
		)