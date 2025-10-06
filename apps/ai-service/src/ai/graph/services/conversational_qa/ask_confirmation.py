# from langchain.prompts import PromptTemplate 
# from typing import Any, Dict, List, Optional

# from ...models.conversational_qa import (
# 	AppointmentRecordModel, 
# 	UserIntentModel,
# 	VerificationRecordModel
	
# )
# from ...types.conversational_qa import IntentType, Routes
# from ...states.conversational_qa import QAState	
# from ...prompts.templates.conversational_qa import ConversationalQAMessages
# from ..llm import LLMService

# from utils import Logger

# logger = Logger(__name__)



# class AskConfirmationService(LLMService):
# 	def __init__(
# 		self, 
# 		model: str = "gpt-4o-mini",
# 		temp: float = 0.0,
# 	) -> None:
# 		super().__init__(model=model, temp=temp)

# 	def run(
# 		self,
# 		user_record: VerificationRecordModel,
# 		user_message: str,
# 		current_intent: IntentType,
# 		appointment_record: AppointmentRecordModel,
# 	) -> Any:
# 		logger.info("[SERVICE] AskConfirmationService")
		
# 		user_name = ""
# 		if user_record:
# 			full_name = user_record.full_name
# 			user_name = full_name.split(" ")[0]
# 		base_prompt = ""
# 		if current_intent == IntentType.CANCEL_APPOINTMENT:
# 			pass

# 		elif current_intent == IntentType.CONFIRM_APPOINTMENT:
# 			pass

		