from ...states.qa import QAState
from ...types.qa import IdentificationState
from ...services.qa import (
	IntentService,
	ExtractionService,
	ValidationService,
	ResponseService
)
from ...types.qa import Nodes, Routes
from utils import Logger

logger = Logger(__name__)


class ProcessUserInputNode:
	def __init__(
		self, 
		intent_service: IntentService, 
		extract_service: ExtractionService, 
		validate_service: ValidationService, 
		response_service: ResponseService
	) -> None:
		
		self.intent = intent_service
		self.extract = extract_service
		self.validate = validate_service
		self.respond = response_service

	def __call__(self, state: QAState) -> QAState:
		logger.info(f"[NODE] Processing user input - step: {state.get('verification_step')}")
		user_message = state.get("user_message", "").strip()
		step = state.get("verification_step", "name")
		collected = state.get("collected_info", {})
		history = state.get("messages", [])
		
		logger.info(f"step = {step}")
		state["current_node"] = Nodes.PROCESS_USER_INPUT
		
		intent = self.intent.run(
			user_message=user_message, 
			verification_step=step, 
			history=history
		)
		logger.info(f"User intent: {intent}")

		if intent.wants_to_skip:
			message = self.respond.run(
				{
					"action": "handle_skip_request",
					"step": step,
					"user_name": collected.get("name"),
				}
			)

			state["messages"] = state.get("messages", []) + [message]
			state["route"] = Routes.COLLECT_NEXT

			return state
				
		if intent.is_asking_question:
			message = self.respond.run(
				{
					"action": "answer_question",
					"step": step,
					"question": user_message,
				}
			)

			state["messages"] = state.get("messages", []) + [message]
			state["route"] = Routes.COLLECT_NEXT

			return state

		result = self.extract.run(user_message, step, collected)

		if result.requires_clarification:
			message = self.respond.run(
				{
					"action": "request_clarification",
					"step": step,
					"message": result.clarification_message,
					"user_input": user_message
				}
			)
			
			state["messages"] = state.get("messages", []) + [message]
			state["route"] = Routes.INVALID_INPUT
			state["error_message"] = "error_message"

			return state

		if result.has_relevant_info and result.extracted_value:
			validation_result = self.validate.run(result.extracted_value, step)
			if validation_result.is_valid and validation_result.cleaned_value:
				logger.info(f"Validated {step}: {validation_result.cleaned_value}")
				collected[step] = validation_result.cleaned_value
				if step == "name":
					state["verification_step"] = "phone"
				elif step == "phone":
					state["verification_step"] = "dob"
				elif step == "dob":
					state["verification_step"] = "complete"

				route = Routes.VERIFY if state["verification_step"] == "complete" else Routes.COLLECT_NEXT

				state["route"] = route
				state["error_message"] = "error_message"
				state["collected_info"] = collected

				return state

			message = self.respond.run(
				{
					"action": "validation_error",
					"step": step,
					"error": validation_result.error_message,
					"suggestions": validation_result.suggestions,
					"user_input": result.extracted_value
				}
			)

			state["messages"] = state.get("messages", []) + [message]
			state["route"] = Routes.INVALID_INPUT
			state["error_message"] = message


			return state

		message = self.respond.run(
			{
				"action": "no_info_found",
				"step": step,
				"user_message": user_message
			}
		)

		state["messages"] = state.get("messages", []) + [message]
		state["route"] = Routes.INVALID_INPUT
		state["error_message"] = message
		

		return state
	
