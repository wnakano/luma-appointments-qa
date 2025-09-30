from abc import ABC, abstractmethod


class ServiceModule(ABC):
    """Abstract base class for service modules"""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the service module"""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup resources when shutting down"""
        pass
    
    @abstractmethod
    def register_tools(self, app) -> None:
        """Register tools with the FastMCP app"""
        pass
