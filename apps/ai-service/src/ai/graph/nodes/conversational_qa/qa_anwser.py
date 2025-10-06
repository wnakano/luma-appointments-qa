from ...states.conversational_qa import QAState
from ...types.conversational_qa import (
	Nodes,
	Routes, 
	IntentType
)
from ...services.conversational_qa import QAAnswerService
from ...models.conversational_qa import QAAnswerModel
from utils import Logger

logger = Logger(__name__)


class QAAnswerNode:
	def __init__(
		self,
		qa_service: QAAnswerService
	) -> None:
		self.qa_service = qa_service
	
	def __call__(self, state: QAState) -> QAState:
		logger.info("[NODE] QAAnswerNode")
		qa_result = self.qa_service.run(
			state=state
		)
		system_message: QAAnswerModel = qa_result.qa_answer
		user_message = state.get("user_message", "")

		state["messages"] = state.get("messages", []) + [
			{
				"user_message": user_message,
				"system_message": system_message
			}
		]
		state["current_node"] = Nodes.QA_ANSWER

		return state

