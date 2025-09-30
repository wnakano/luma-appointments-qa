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
from .types.qa import (
	Nodes,
	Routes,
	MenuType,
	FlowPhase,
	IdentificationState,
	UserSession
)
from .services.qa import (
	ExtractionService,
	ValidationService,
	IntentService,
	ResponseService,
	QueryToolService,
	QueryORMService
)

from .nodes.qa import (
	VerificationStepTracker,
	CheckUserSessionNode,
	ProcessUserInputNode,
	CollectUserInfoNode,
	HandleInvalidInputNode,
	VerifyIdentityNode,
	QueryIdentityNode,
	VerificationFailedNode,
	MenuNodeInput,
	MenuNodeOutput,
	ActionAppointmentNode
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
		
		# mermaid_mmd = self._graph.get_graph().draw_mermaid()
		# mermaid_mmd_path = Path("/app/images/qa_graph.mmd")
		# mermaid_mmd_path.write_text(mermaid_mmd)

	def _define_nodes(self) -> Dict[str, Any]:
		"""Instantiate all nodes with their required services"""

		intent_service = IntentService(model="gpt-4o-mini", temp=0.1)
		extract_service = ExtractionService(model="gpt-4o-mini", temp=0.1)
		validate_service = ValidationService(model="gpt-4o-mini", temp=0.1)
		response_service = ResponseService(model="gpt-4o-mini", temp=0.1)
		query_tool_service = QueryToolService(model="gpt-4o-mini", temp=0.0)
		query_orm_service = QueryORMService()

		nodes = {
			Nodes.CHECK_USER_SESSION: CheckUserSessionNode(response_service=response_service),
			Nodes.PROCESS_USER_INPUT: ProcessUserInputNode(
				intent_service=intent_service, 
				extract_service=extract_service, 
				validate_service=validate_service, 
				response_service=response_service
			),
			Nodes.COLLECT_USER_INFO: CollectUserInfoNode(response_service=response_service),
			Nodes.HANDLE_INVALID_INPUT: HandleInvalidInputNode(),
			Nodes.VERIFY_IDENTITY: VerifyIdentityNode(response_service=response_service),
			Nodes.QUERY_IDENTITY: QueryIdentityNode(
				query_tool_service=query_tool_service,
				response_service=response_service
			),
			Nodes.VERIFICATION_FAILED: VerificationFailedNode(response_service=response_service),
			Nodes.MENU_INPUT: MenuNodeInput(
				response_service=response_service,
				query_service=query_orm_service
			),
			Nodes.MENU_OUTPUT: MenuNodeOutput(
				response_service=response_service,
				query_service=query_orm_service
			),
			Nodes.ACTION_APPOINTMENT_LIST: ActionAppointmentNode(
				response_service=response_service,
				query_service=query_orm_service
			),

		}
		return nodes
	
	def _get_interrupt_configuration(self) -> Dict[str, List[str]]:
		"""Define which nodes should have interrupts"""
		return {
			"interrupt_before": [

				Nodes.ACTION_APPOINTMENT_LIST   # Wait before executing action
			],
			
			"interrupt_after": [
				Nodes.COLLECT_USER_INFO,  	 	# Wait after asking for user info
				Nodes.HANDLE_INVALID_INPUT,  	# Wait after error message
				Nodes.VERIFICATION_FAILED,   	# Wait after verification failure
				Nodes.MENU_INPUT,         		# Wait after showing menu
			]
		}

	def _should_auto_verify(self, state: QAState) -> bool:
		"""Check if we should automatically trigger verification"""
		verification_step = state.get("verification_step", "")
		collected_info = state.get("collected_info", {})
		route = state.get("route", "")
		
		logger.info(f"Checking auto-verify: step={verification_step}, route={route}, collected={list(collected_info.keys())}")
		
		if verification_step == "dob":
			if VerificationStepTracker.is_complete(collected_info):
				logger.info(f"Auto-verify triggered: All required fields collected: {list(collected_info.keys())}")
				return True
			else:
				missing = VerificationStepTracker.get_missing_steps(collected_info)
				logger.info(f"DOB step but missing fields: {missing}")

		if route == Routes.VERIFY and VerificationStepTracker.is_complete(collected_info):
			logger.info(f"Auto-verify triggered: Route is 'verify' and all fields collected")
			return True
				
		return False

	def _handle_auto_verification_flow(self, state: QAState, config: Dict) -> QAState:
		"""
		Handle automatic verification flow when all info is collected.
		Sets up state for verification and lets graph edges handle the flow.
		"""
		logger.info("Starting auto-verification flow")
		
		try:
			state["route"] = Routes.VERIFY
			state["phase"] = "verification"
			
			self._graph.update_state(config=config, values=state)
			
			result = self._graph.invoke(input=None, config=config)
			
			logger.info(f"Auto-verification completed: current_node={result.get('current_node')}, route={result.get('route')}")
			
			return result
			
		except Exception as e:
			logger.error(f"Error in auto-verification flow: {e}")
			import traceback
			logger.error(f"Traceback: {traceback.format_exc()}")
			
			state["route"] = Routes.WAIT
			state["error_message"] = "Verification process encountered an error. Please try again."
			state["phase"] = "collection"
			
			self._graph.update_state(
				config=config,
				values=state,
				as_node=Nodes.COLLECT_USER_INFO
			)
			
			return state
		
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

		graph.set_entry_point(Nodes.CHECK_USER_SESSION)

		graph.add_conditional_edges(
			Nodes.CHECK_USER_SESSION,
			lambda s: s.get("route", "collect"),
			{
				Routes.MISSING: Nodes.COLLECT_USER_INFO,
				Routes.VERIFIED: Nodes.VERIFY_IDENTITY,
				Routes.IDENTIFIED: Nodes.MENU_INPUT
			}
		)

		graph.add_conditional_edges(
			Nodes.PROCESS_USER_INPUT,
			lambda s: s.get("route", "collect_next"),
			{
				Routes.COLLECT_NEXT: Nodes.COLLECT_USER_INFO,
				Routes.INVALID_INPUT: Nodes.HANDLE_INVALID_INPUT,
				Routes.VERIFY: Nodes.VERIFY_IDENTITY,
			}
		)

		graph.add_edge(Nodes.HANDLE_INVALID_INPUT, END)

		graph.add_conditional_edges(
			Nodes.COLLECT_USER_INFO,
			lambda s: s.get("route", "wait"),
			{
				Routes.VERIFY: Nodes.VERIFY_IDENTITY,
				Routes.PROCESS_USER_INPUT: Nodes.PROCESS_USER_INPUT,
			}
		)

		graph.add_conditional_edges(
			Nodes.VERIFY_IDENTITY,
			lambda s: s.get("route", "verified"),
			{
				Routes.VERIFIED: Nodes.QUERY_IDENTITY,
				Routes.RETRY: Nodes.COLLECT_USER_INFO,
				Routes.FAILED: END,
			}
		)

		graph.add_conditional_edges(
			Nodes.QUERY_IDENTITY,
			lambda s: s.get("route", "not_match"),
			{
				Routes.MATCH: Nodes.MENU_INPUT,
				Routes.NOT_MATCH: Nodes.VERIFICATION_FAILED
			}
		)

		graph.add_edge(Nodes.VERIFICATION_FAILED, Nodes.COLLECT_USER_INFO)

		graph.add_edge(Nodes.MENU_INPUT, Nodes.MENU_OUTPUT)
		graph.add_conditional_edges(
			Nodes.MENU_OUTPUT,
			lambda s: s.get("route", "wrong_appointment_choice"),
			{
				Routes.WAIT_APPOINTMENT_ACTION: Nodes.ACTION_APPOINTMENT_LIST,
				Routes.WRONG_APPOINTMENT_CHOICE: Nodes.MENU_INPUT
			}
		)
		graph.add_conditional_edges(
			Nodes.ACTION_APPOINTMENT_LIST,
			lambda s: s.get("route", "wrong_action_choice"),
			{
				Routes.CORRECT_APPOINTMENT_ACTION: Nodes.MENU_INPUT,
				Routes.WRONG_ACTION_CHOICE: Nodes.MENU_OUTPUT
			}
		)

		interrupt_config = self._get_interrupt_configuration()
		
		checkpointer = PostgresCheckpointer().get_checkpointer()

		compiled = graph.compile(
			checkpointer=checkpointer,
			interrupt_before=interrupt_config["interrupt_before"],
			interrupt_after=interrupt_config["interrupt_after"]
		)

		logger.info("QA graph compiled with Postgres checkpointer and interrupt configuration")

		return compiled

	def _cfg(self, session_id: str) -> Dict[str, Dict[str, str]]:
		return {"configurable": {"thread_id": session_id}}

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
			messages=[user_message],
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
		
		if self._should_auto_verify(updated_state):
			logger.info("Auto-verification triggered during collection")
			return self._handle_auto_verification_flow(updated_state, config)
		
		interrupt_status = self.get_interrupt_status(session_id)
		
		if interrupt_status.get("interrupted"):
			next_nodes = interrupt_status.get("next_nodes", [])
			logger.info(f"Resuming from interrupt, next nodes: {next_nodes}")
			
			self._graph.update_state(config=config, values=updated_state)
			
			try:
				result = self._graph.invoke(input=None, config=config)
				return result
			except Exception as e:
				logger.error(f"Error continuing from interrupt: {e}")
				return self._fallback_to_normal_flow(updated_state, config)
		
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