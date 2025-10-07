from typing import Optional

from ...states.conversational_qa import QAState, StateKeys
from ...types.conversational_qa import (
	Nodes,
	Routes, 
	MessageKeys
)
from ...models.conversational_qa import VerificationInfoModel, AppointmentInfoModel
from ...services.conversational_qa import ClarificationService
from utils import Logger

logger = Logger(__name__)


class ClarificationNode:
	def __init__(self, clarification_service: ClarificationService) -> None:
		self.clarification_service = clarification_service
	
	def __call__(self, state: QAState) -> QAState:
		try:
			logger.info("[NODE] ClarificationNode")
			
			current_node = state.get(StateKeys.CURRENT_NODE)
			route = state.get(StateKeys.ROUTE)
			user_message = state.get(StateKeys.USER_MESSAGE, "")
			messages = state.get(StateKeys.MESSAGES, [])

			system_prompt = self._generate_clarification_prompt(state, current_node, route)
			
			self._update_request_counters(state, current_node)

			state[StateKeys.CURRENT_NODE] = Nodes.CLARIFICATION
			state[StateKeys.MESSAGES] = messages + [
				{
					MessageKeys.USER_MESSAGE: user_message,
					MessageKeys.SYSTEM_MESSAGE: system_prompt
				}
			]
			
			logger.info(f" ... Generated clarification for node: {current_node}")
			
			return state
			
		except Exception as e:
			logger.error(f"Error in ClarificationNode: {e}", exc_info=True)
			raise
	
	def _generate_clarification_prompt(
		self,
		state: QAState,
		current_node: Optional[Nodes],
		route: Optional[Routes]
	) -> str:
		if current_node == Nodes.VERIFICATION_PATIENT:
			return self._get_user_verification_clarification(state)
		
		elif current_node == Nodes.VERIFICATION_APPOINTMENT:
			return self._get_appointment_verification_clarification(state)
		
		elif route == Routes.INTENT_WAIT and current_node == Nodes.ACTION_ROUTER:
			return self._get_appointment_wait_clarification(state)
		
		else:
			error_msg = (
				f"Unable to generate clarification for node: {current_node}, route: {route}"
			)
			logger.error(error_msg)
			raise ValueError(error_msg)
	
	def _get_user_verification_clarification(self, state: QAState) -> str:
		verification_info: Optional[VerificationInfoModel] = state.get(
			StateKeys.USER_INFO
		)
		
		logger.info(" ... Generating user verification clarification")
		
		system_prompt = self.clarification_service.user_run(
			verification_info=verification_info
		)
		
		return system_prompt
	
	def _get_appointment_verification_clarification(self, state: QAState) -> str:
		appointment_info: Optional[AppointmentInfoModel] = state.get(
			StateKeys.APPOINTMENT_INFO
		)
		
		logger.info(" ... Generating appointment verification clarification")
		
		system_prompt = self.clarification_service.appointment_run(
			appointment_info=appointment_info
		)
		
		return system_prompt
	
	def _get_appointment_wait_clarification(self, state: QAState) -> str:
		appointment_info: Optional[AppointmentInfoModel] = state.get(
			StateKeys.APPOINTMENT_INFO
		)
		
		logger.info(" ... Generating appointment wait clarification")
		
		system_prompt = self.clarification_service.appointment_wait(
			appointment_info=appointment_info
		)
		
		return system_prompt
	
	def _update_request_counters(
		self,
		state: QAState,
		current_node: Optional[Nodes]
	) -> None:
		if current_node == Nodes.VERIFICATION_PATIENT:
			current_count = state.get(StateKeys.USER_REQUEST_COUNTER, 0)
			state[StateKeys.USER_REQUEST_COUNTER] = current_count + 1
			logger.info(f" ... Updated user_request_counter to {current_count + 1}")
		
		elif current_node == Nodes.VERIFICATION_APPOINTMENT:
			current_count = state.get(StateKeys.APPOINTMENT_REQUEST_COUNTER, 0)
			state[StateKeys.APPOINTMENT_REQUEST_COUNTER] = current_count + 1
			logger.info(f" ... Updated appointment_request_counter to {current_count + 1}")