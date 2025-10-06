from typing import (
	List, 
	Optional, 
	Union
)

from ...states.conversational_qa import QAState, StateKeys
from ...services.conversational_qa import IntentService
from ...types.conversational_qa import (
	Nodes,
	Routes, 
	IntentType
)
from ...models.conversational_qa import (
	ConversationIntentModel,
	VerificationInfoModel,
	AppointmentInfoModel
)
from utils import Logger

logger = Logger(__name__)


class ConversationManagerNode:
	APPOINTMENT_INTENTS = {
		IntentType.LIST_APPOINTMENTS,
		IntentType.CONFIRM_APPOINTMENT,
		IntentType.CANCEL_APPOINTMENT,
		IntentType.USER_INFORMATION,
		IntentType.APPOINTMENT_INFORMATION
	}
	INFO_UPDATE_INTENTS = {
		IntentType.USER_INFORMATION, 
		IntentType.APPOINTMENT_INFORMATION
	}

	INFO_PATIENT_KEYS: List[str] = ["full_name", "phone_number", "date_of_birth"]
	INFO_APPOINTMENT_KEYS: List[str] = ["doctor_full_name", "clinic_name", "appointment_date", "specialty"]
	
	def __init__(
		self,
		intent_service: IntentService
	) -> None:
		self.intent_service = intent_service
	
	def __call__(self, state: QAState) -> QAState:
		logger.info("[NODE] ConversationManagerNode")
		is_verified = state.get(StateKeys.IS_VERIFIED, False)
		user_info = state.get(StateKeys.USER_INFO)
		appointment_info = state.get(StateKeys.APPOINTMENT_INFO)
		current_intent = state.get(StateKeys.CURRENT_INTENT)
		
		# Get intent from service
		intent_result: ConversationIntentModel = self.intent_service.run(state=state)
		user_intent = intent_result.user_intent.intent_type
		
		# Update current intent
		state[StateKeys.CURRENT_INTENT] = self._determine_current_intent(
			current_intent, user_intent
		)
		
		logger.info(f" ... Current intent: {current_intent}")
		logger.info(f" ... User intent: {user_intent}")
		logger.info(f" ... Updated intent: {state[StateKeys.CURRENT_INTENT]}")
		
		route = self._determine_route(user_intent=user_intent)
		
		if user_intent in self.APPOINTMENT_INTENTS:
			self._handle_appointment_intent(
				state=state, 
				intent_result=intent_result, 
				is_verified=is_verified, 
				user_info=user_info, 
				appointment_info=appointment_info
			)
		
		# Update state with routing info
		state[StateKeys.ROUTE] = route
		state[StateKeys.CURRENT_NODE] = Nodes.CONVERSATION_MANAGER
		
		logger.info(f" ... Route set to: {route}")
		
		return state
	
	def _determine_current_intent(
		self, 
		current_intent: Optional[IntentType], 
		user_intent: IntentType
	) -> IntentType:
		""" Determine which intent should be current."""
		if current_intent and user_intent in self.INFO_UPDATE_INTENTS:
			logger.info(f" ... Keeping previous intent: {current_intent}")
			return current_intent
		return user_intent

	def _handle_appointment_intent(
		self,
		state: QAState,
		intent_result: ConversationIntentModel,
		is_verified: bool,
		user_info: Optional[object],
		appointment_info: Optional[object]
	) -> None:
		"""Handle appointment-related intent processing."""
		if not is_verified:
			verification_info = getattr(intent_result, "verification_info", None)
			if verification_info:
				state[StateKeys.USER_INFO] = self._update_info(
					user_info,
					verification_info,
					self.INFO_PATIENT_KEYS,
					"user_info"
				)
		
		new_appointment_info = getattr(intent_result, "appointment_info", None)
		if new_appointment_info:
			state[StateKeys.APPOINTMENT_INFO] = self._update_info(
				appointment_info,
				new_appointment_info,
				self.INFO_APPOINTMENT_KEYS,
				"appointment_info"
			)
	
	def _determine_route(self, user_intent: IntentType) -> Routes:
		"""Determine the route based on user intent."""
		if user_intent == IntentType.GENERAL_QA:
			return Routes.ACTION_QA
		elif user_intent in self.APPOINTMENT_INTENTS:
			return Routes.ACTION_APPOINTMENT

		return Routes.ACTION_QA
		
	def _update_info(
		self, 
		current_info: Union[VerificationInfoModel, AppointmentInfoModel], 
		new_info: Union[VerificationInfoModel, AppointmentInfoModel], 
		keys: List[str],
		info_type: str
	) -> Union[VerificationInfoModel, AppointmentInfoModel]:
		if not new_info:
			return current_info
		
		if current_info:
			for key in keys:
				existing_value = getattr(current_info, key, None)
				new_value = getattr(new_info, key, None)
				if not existing_value and new_value:
					setattr(current_info, key, new_value)
			logger.info(f" ... {info_type} UPDATED: {current_info}")
			return current_info
		else:
			logger.info(f" ... {info_type} ADDED: {new_info}")
			return new_info