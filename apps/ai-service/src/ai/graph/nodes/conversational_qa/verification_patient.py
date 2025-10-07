from typing import Dict, List, Optional

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
			
			route, user_record = self._verify_user(verification_info)

			if route == Routes.VERIFIED:
				state[StateKeys.USER_RECORD] = user_record
				state[StateKeys.IS_VERIFIED] = True
				logger.info(f" ... User verified: {user_record.full_name}")
			else:
				state[StateKeys.USER_RECORD] = None
				state[StateKeys.IS_VERIFIED] = False
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
	) -> tuple[Routes, Optional[VerificationRecordModel]]:

		if not verification_info:
			logger.info(" ... No verification info provided")
			return Routes.NOT_VERIFIED, None

		logger.info(" ... Querying database for user")
		user_records: List[Dict] = self.query_orm_service.find_user(
			user_info=verification_info
		)

		if not user_records or len(user_records) == 0:
			logger.info(" ... No matching user found in database")
			return Routes.NOT_VERIFIED, None
		
		if len(user_records) > 1:
			logger.warning(
				f" ... Multiple users found ({len(user_records)}), using first match"
			)
		
		user_data = user_records[0]
		user_record = self._create_user_record(user_data)
		
		logger.info(f" ... User found: ID={user_record.user_id}")
		
		return Routes.VERIFIED, user_record
	
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