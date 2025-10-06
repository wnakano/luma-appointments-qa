from typing import Optional

from ...states.conversational_qa import QAState, StateKeys
from ...types.conversational_qa import (
	Nodes,
	MessageKeys
)
from ...services.conversational_qa import QAAnswerService
from ...models.conversational_qa import QAAnswerModel
from utils import Logger

logger = Logger(__name__)


class QAAnswerNode:
	def __init__(self, qa_service: QAAnswerService) -> None:
		self.qa_service = qa_service
	
	def __call__(self, state: QAState) -> QAState:
		try:
			logger.info("[NODE] QAAnswerNode")
			
			user_message = state.get(StateKeys.USER_MESSAGE, "")
			messages = state.get(StateKeys.MESSAGES, [])
			
			qa_result: QAAnswerModel = self.qa_service.run(state=state)
			
			qa_answer = qa_result.qa_answer

			state[StateKeys.MESSAGES] = messages + [
				{
					MessageKeys.USER_MESSAGE: user_message,
					MessageKeys.SYSTEM_MESSAGE: qa_answer
				}
			]
			state[StateKeys.CURRENT_NODE] = Nodes.QA_ANSWER
			
			return state
			
		except Exception as e:
			logger.error(f"Error in QAAnswerNode: {e}", exc_info=True)
			raise
