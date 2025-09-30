from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseGraph(ABC):

	@abstractmethod
	def _define_nodes(self) -> Any:
		"""Define and instantiate all nodes in the graph."""
		pass

	@abstractmethod
	def _define_graph(self) -> Any:
		"""Define the graph structure and connections."""
		pass    
	
	def _cfg(self, session_id: str) -> Dict[str, Dict[str, str]]:
		return {"configurable": {"thread_id": session_id}}
