from pathlib import Path
from typing import (
	Any, 
	Dict,
	Optional,
	List
)

from langgraph.graph import (
	START,
	END, 
	StateGraph,
) 
from langgraph.graph.state import CompiledStateGraph

from .states.qa import QAState
from .checkpointer.postgres import PostgresCheckpointer
from .types.conversational_qa import (
	Nodes,
	Routes,
	FlowPhase
)
from .services.conversational_qa import (
	IntentService,
	QAAnswerService,
	QueryORMService,
	AppointmentMatchService,
	ProcessConfirmationService,
	ClarificationService
)

from .nodes.conversational_qa import (
	ConversationManagerNode,
	QAAnswerNode,
	VerificationGateNode,
	VerificationPatientNode,
	VerificationAppointmentNode,
	ClarificationNode,
	ActionRouterNode,
	ListAppointmentsNode,
	ConfirmAppointmentNode,
	CancelAppointmentNode,
	AskConfirmationNode,
	ProcessConfirmationNode,
	ActionResponseNode
)


from utils import (
	Logger, 
	TimeHandler,
	UUIDHandler
)

from .base import BaseGraph

logger = Logger(__name__)


class QAGraph(BaseGraph):
	def __init__(self) -> None:
		super().__init__()
		self._nodes = self._define_nodes()
		self._graph = self._define_graph()
		
		mermaid_mmd = self._graph.get_graph().draw_mermaid()
		mermaid_mmd_path = Path("/app/images/qa-graph-2.mmd")
		mermaid_mmd_path.write_text(mermaid_mmd)

	def _define_nodes(self) -> Dict[str, Any]:
		"""Instantiate all nodes with their required services"""

		intent_service = IntentService(model="gpt-4o-mini", temp=0.0)
		qa_service = QAAnswerService(model="gpt-4o-mini", temp=0.3)
		query_orm_service = QueryORMService()
		appointment_match_service = AppointmentMatchService(query_orm_service=query_orm_service)
		process_confirmation_service = ProcessConfirmationService(model="gpt-4o-mini", temp=0.0)
		clarification_service = ClarificationService()

		nodes = {
			Nodes.CONVERSATION_MANAGER: ConversationManagerNode(intent_service=intent_service),
			Nodes.QA_ANSWER: QAAnswerNode(qa_service=qa_service),
			Nodes.VERIFICATION_GATE: VerificationGateNode(query_orm_service=query_orm_service),
			Nodes.VERIFICATION_PATIENT: VerificationPatientNode(query_orm_service=query_orm_service),
			Nodes.VERIFICATION_APPOINTMENT: VerificationAppointmentNode(
				query_orm_service=query_orm_service,
				appointment_match_service=appointment_match_service
			),
			Nodes.CLARIFICATION: ClarificationNode(
				clarification_service=clarification_service
			),
			Nodes.ACTION_ROUTER: ActionRouterNode(),
			Nodes.LIST_APPOINTMENTS: ListAppointmentsNode(),
			Nodes.CONFIRM_APPOINTMENTS: ConfirmAppointmentNode(query_orm_service=query_orm_service),
			Nodes.CANCEL_APPOINTMENTS: CancelAppointmentNode(query_orm_service=query_orm_service),
			Nodes.ASK_CONFIRMATION: AskConfirmationNode(),
			Nodes.PROCESS_CONFIRMATION: ProcessConfirmationNode(
				query_orm_service=query_orm_service,
				process_confirmation_service=process_confirmation_service
			),
			Nodes.ACTION_RESPONSE: ActionResponseNode(),
		}
		return nodes
	
	def _get_interrupt_configuration(self) -> Dict[str, List[str]]:
		"""Define which nodes should have interrupts"""
		return {
			"interrupt_before": [
			],
			
			"interrupt_after": [
				Nodes.QA_ANSWER,
				Nodes.CLARIFICATION,
				Nodes.ASK_CONFIRMATION,
				Nodes.ACTION_RESPONSE
			]
		}
	
	def _fallback_to_normal_flow(self, state: QAState, config: Dict) -> QAState:
		"""Fallback to normal graph execution"""
		try:
			return self._graph.invoke(input=state, config=config)
		except Exception as e:
			logger.error(f"Fallback to normal flow failed: {e}")
			return state
		
	def _define_graph(self) -> CompiledStateGraph:
		"""Define the graph with interrupt configuration"""

		graph = StateGraph(QAState)
		
		for name, node in self._nodes.items():
			graph.add_node(name, node)

		graph.set_entry_point(Nodes.CONVERSATION_MANAGER)

		graph.add_conditional_edges(
			Nodes.CONVERSATION_MANAGER,
			lambda state: state.get("route", Routes.ACTION_APPOINTMENT),
			{
				Routes.ACTION_QA: Nodes.QA_ANSWER,
				Routes.ACTION_APPOINTMENT: Nodes.VERIFICATION_GATE
			}
		)
		graph.add_edge(Nodes.QA_ANSWER, Nodes.CONVERSATION_MANAGER)

		graph.add_conditional_edges(
			Nodes.VERIFICATION_GATE,
			lambda state: state.get("route", "collect"),
			{
				Routes.USER_VERIFICATION: Nodes.VERIFICATION_PATIENT,
				Routes.APPOINTMENT_VERIFICATION: Nodes.VERIFICATION_APPOINTMENT,
				Routes.VERIFIED: Nodes.ACTION_ROUTER,
			}
		)
		graph.add_conditional_edges(
			Nodes.VERIFICATION_PATIENT, 
			lambda state: state.get("route", "collect"),
			{
				Routes.NOT_VERIFIED: Nodes.CLARIFICATION,
				Routes.VERIFIED: Nodes.VERIFICATION_APPOINTMENT,
			}
		)
		graph.add_conditional_edges(
			Nodes.VERIFICATION_APPOINTMENT,
			lambda state: state.get("route", "collect"),
			{
				Routes.NOT_VERIFIED: Nodes.CLARIFICATION,
				Routes.VERIFIED: Nodes.ACTION_ROUTER,
			}
		)

		graph.add_conditional_edges(
			Nodes.ACTION_ROUTER,
			lambda state: state.get("route", "collect_next"),
			{
				Routes.INTENT_WAIT: Nodes.CLARIFICATION,
				Routes.INTENT_LIST: Nodes.LIST_APPOINTMENTS,
				Routes.INTENT_CONFIRM: Nodes.ASK_CONFIRMATION,
				Routes.INTENT_CANCEL: Nodes.ASK_CONFIRMATION,
			}
		)
		graph.add_edge(Nodes.LIST_APPOINTMENTS, Nodes.ACTION_RESPONSE)
	
		graph.add_edge(Nodes.ASK_CONFIRMATION, Nodes.PROCESS_CONFIRMATION)
		graph.add_conditional_edges(
			Nodes.PROCESS_CONFIRMATION,
			lambda state: state.get("route", Routes.ACTION_REJECTED),
			{
				Routes.ACTION_CONFIRMED: Nodes.ACTION_RESPONSE,
				Routes.ACTION_REJECTED: Nodes.ACTION_RESPONSE,
				Routes.ACTION_UNCLEAR: Nodes.ASK_CONFIRMATION
			}
		)

		
		graph.add_edge(Nodes.CLARIFICATION, Nodes.CONVERSATION_MANAGER)

		graph.add_edge(Nodes.ACTION_RESPONSE, Nodes.CONVERSATION_MANAGER)

		interrupt_config = self._get_interrupt_configuration()
		
		checkpointer = PostgresCheckpointer().get_checkpointer()

		compiled = graph.compile(
			checkpointer=checkpointer,
			interrupt_before=interrupt_config["interrupt_before"],
			interrupt_after=interrupt_config["interrupt_after"]
		)

		logger.info("QA graph compiled with Postgres checkpointer and interrupt configuration")

		return compiled

	def get_current_state(self, session_id: str) -> Optional[QAState]:
		try:
			snap = self._graph.get_state(self._cfg(session_id))
			if snap and getattr(snap, "values", None):
				logger.info(f"Found existing state for session {session_id}")
				if hasattr(snap, 'next') and snap.next:
					logger.info(f"Session {session_id} is at interrupt point, next nodes: {snap.next}")
				return snap.values
			logger.info(f"No existing state for session {session_id}")
			return None
		except Exception as e:
			logger.error(f"get_current_state error: {e}")
			return None

	def new_state(
		self, 
		request_id: str, 
		session_id: str, 
		user_message: str
	) -> QAState:
		
		initial_state = QAState(
			request_id=request_id,
			session_id=session_id,
			user_message=user_message,
			history=[],
			messages=[],
			user_verified=False,
			verification_step="name",
			collected_info={},
			user_info={},
			user_info_db={},
			current_node="",
			route="",
			error_message=None,
			retry_count=0,
			assistant_message=None,
			appointments=None,
			selected_appoint=None,
			menu_options=None,
			selected_action=None,
			selected_menu_choice=None,
			phase="initial",
			verification_attempts=0,
			invalid_menu_attempts=0
		)

		return self._graph.invoke(
			input=initial_state, 
			config=self._cfg(session_id)
		)
		
	def get_interrupt_status(self, session_id: str) -> Dict[str, Any]:
		"""Get detailed interrupt status for a session"""
		try:
			snap = self._graph.get_state(self._cfg(session_id))
			if not snap:
				return {"interrupted": False, "message": "No state found"}
			
			return {
				"interrupted": bool(hasattr(snap, 'next') and snap.next),
				"next_nodes": getattr(snap, 'next', []),
				"current_state": snap.values if hasattr(snap, 'values') else None,
				"waiting_for_user": bool(hasattr(snap, 'next') and snap.next)
			}
		except Exception as e:
			logger.error(f"Error getting interrupt status: {e}")
			return {"interrupted": False, "error": str(e)}

	def debug_graph_state(self, session_id: str) -> Dict[str, Any]:
		"""Debug method to inspect full graph state"""
		try:
			snap = self._graph.get_state(self._cfg(session_id))
			
			debug_info = {
				"has_state": snap is not None,
				"has_values": hasattr(snap, 'values') if snap else False,
				"has_next": hasattr(snap, 'next') if snap else False,
				"next_nodes": getattr(snap, 'next', []) if snap else [],
				"interrupted": bool(hasattr(snap, 'next') and snap.next) if snap else False,
			}
			
			if snap and hasattr(snap, 'values'):
				values = snap.values
				debug_info.update({
					"current_node": values.get("current_node"),
					"route": values.get("route"),
					"phase": values.get("phase"),
					"user_verified": values.get("user_verified"),
					"verification_step": values.get("verification_step"),
					"message_count": len(values.get("messages", [])),
					"has_assistant_message": bool(values.get("assistant_message")),
					"menu_options_count": len(values.get("menu_options", {})) if values.get("menu_options") else 0
				})
			
			return debug_info
			
		except Exception as e:
			return {"error": str(e), "has_state": False}

	def resume_state(
		self, 
		request_id: str, 
		session_id: str, 
		user_message: str, 
		retrieved: QAState
	) -> QAState:
		"""Resumption using interrupt-based flow control"""
		
		config = self._cfg(session_id)
		
		existing_messages = retrieved.get("messages") or []
		updated_state = QAState(**retrieved)
		updated_state["request_id"] = request_id
		updated_state["user_message"] = user_message
		updated_state["messages"] = existing_messages + [user_message]
		
		current_node = retrieved.get("current_node", "")
		phase = retrieved.get("phase", "")
		
		logger.info(f"Resume session {session_id}: node={current_node}, phase={phase}")
		
		# if self._should_auto_verify(updated_state):
		# 	logger.info("Auto-verification triggered during collection")
		# 	return self._handle_auto_verification_flow(updated_state, config)
		
		interrupt_status = self.get_interrupt_status(session_id)
		
		if interrupt_status.get("interrupted"):
			next_nodes = interrupt_status.get("next_nodes", [])
			logger.info(f"Resuming from interrupt, next nodes: {next_nodes}")
			
			self._graph.update_state(config=config, values=updated_state)
			
			# try:
			result = self._graph.invoke(input=None, config=config)
			return result
			# except Exception as e:
			# 	logger.error(f"Error continuing from interrupt: {e}")
			# 	return self._fallback_to_normal_flow(updated_state, config)
		
		logger.info("Non-interrupted session, continuing with normal flow")
		return self._fallback_to_normal_flow(updated_state, config)

	async def __call__(
		self, 
		user_message: str, 
		request_id: str, 
		session_id: Optional[str]
	) -> QAState:

		if session_id is None:
			session_id = str(UUIDHandler.new_uuid())
			logger.info(f"Generated new session_id: {session_id}")

		existing = self.get_current_state(session_id)
		if existing:
			logger.info(f"Resuming session {session_id}")
			state = self.resume_state(request_id, session_id, user_message, existing)
		else:
			logger.info(f"Starting new session {session_id}")
			state = self.new_state(request_id, session_id, user_message)

		logger.info(f"Final state for session {session_id}:")
		logger.info(f"  - current_node: {state.get('current_node')}")
		logger.info(f"  - route: {state.get('route')}")
		logger.info(f"  - phase: {state.get('phase')}")
		# print("##############################################################################")
		# print(state)
		# print("##############################################################################")
		return state