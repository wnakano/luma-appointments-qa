from abc import ABC, abstractmethod
from typing import Any


class BaseGraph(ABC):

    @abstractmethod
    def _define_nodes(self) -> Any:
        """Define and instantiate all nodes in the graph."""
        pass

    @abstractmethod
    def _define_graph(self) -> Any:
        """Define the graph structure and connections."""
        pass    

