import os
from contextlib import asynccontextmanager

from typing import Dict, Optional, List, Any, Tuple
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.requests import Request


from fastmcp import FastMCP
from services import ServiceModule
from utils import Logger

logger = Logger(__name__)


class ModularMCPServer:
	"""Coordinator for multiple service modules wrapping a FastMCP instance.

	Supports deployment modes:
		- STDIO (local dev)
		- Direct HTTP (transport="http")
		- Streamable HTTP (SSE) transport
		- ASGI app mounting via http_app()
	"""

	def __init__(self, name: str = "Modular MCP Server"):
		self.name = name
		self.services: Dict[str, ServiceModule] = {}
		self.app: Optional[FastMCP] = None
		self._service_status: Dict[str, Tuple[bool, Optional[str]]] = {}
		self._created = False
	
	def add_service(self, name: str, service: ServiceModule) -> None:
		"""Add a service module to the server"""
		self.services[name] = service
	
	async def initialize_services(self) -> None:
		for name, service in self.services.items():
			try:
				await service.initialize()
				self._service_status[name] = (True, None)
				logger.info(f"Service '{name}' initialized", )
			except Exception as e:
				self._service_status[name] = (False, str(e))
				logger.error(f"Error initializing service '{name}'")
	
	async def cleanup_services(self) -> None:
		for name, service in self.services.items():
			try:
				await service.cleanup()
				logger.info(f"Service '{name}' cleaned up", )
			except Exception as e:
				logger.error(f"Error cleaning service '{name}': {e}")

	async def health_check(self, request: Request):
		return JSONResponse({
			"status": "ok",
			"server": self.name,
			"services": {
				n: {"ok": ok, "error": err} for n, (ok, err) in self._service_status.items()
			},
		})

	async def readiness(self, request: Request):
		failed = [n for n, (ok, _) in self._service_status.items() if not ok]
		return JSONResponse(
			{"status": "ready" if not failed else "degraded", "failed_services": failed},
			status_code=200 if not failed else 503,
		)

	async def list_tools(self, request: Request):
		tools_by_service: Dict[str, List[Any]] = {}
		for name, svc in self.services.items():
			items: List[Any] = []
			list_fn = getattr(svc, "list_tools", None)
			if callable(list_fn):
				try:
					items = list_fn()
				except Exception as e:
					logger.warning(f"list_tools failed for '{name}': {e}")
			tools_by_service[name] = items
		return JSONResponse({"server": self.name, "tools": tools_by_service})

	def create_app(self) -> FastMCP:
		if self._created and self.app:
			return self.app

		@asynccontextmanager
		async def lifespan(app: FastMCP):
			await self.initialize_services()
			try:
				yield
			finally:
				await self.cleanup_services()

		app = FastMCP(self.name, lifespan=lifespan)

		app.custom_route("/mcp/health", methods=["GET"])(self.health_check)
		app.custom_route("/mcp/ready", methods=["GET"])(self.readiness)
		app.custom_route("/mcp/tools", methods=["GET"])(self.list_tools)
	
		for service in self.services.values():
			service.register_tools(app)

		self.app = app
		self._created = True
		return app

	def http_app(self, path: str = "/mcp/"):
		if not self.app:
			self.create_app()
		return self.app.http_app(path=path)

	async def run_stdio(self) -> None:
		if not self.app:
			self.create_app()
		await self.app.run()

	async def run_http(self, host: str = "0.0.0.0", port: int = 8080, path: str = "/mcp/") -> None:
		if not self.app:
			self.create_app()
		await self.app.run(transport="http", host=host, port=port, path=path)

	async def run_streamable(self, host: str = "0.0.0.0", port: int = 8080, path: str = "/mcp/") -> None:
		if not self.app:
			self.create_app()
		await self.app.run_async(
			transport="streamable-http",
			host=host,
			port=port,
			path=path,
		)
		
	async def run(self) -> None:  # stdio
		await self.run_stdio()

	async def run_async(self) -> None:
		port = int(os.getenv("PORT", 8080))
		await self.run_streamable(port=port)
