from typing import Any, Dict, List, Optional
from .base import ServiceModule
from .prompts.todo import WRITE_TODOS_DESCRIPTION, TODO_USAGE_INSTRUCTIONS

from utils import Logger

logger = Logger(__name__)



class TodoService(ServiceModule):
    def __init__(self):
        self._todos: List[Dict[str, Any]] = []
        self._tools_meta: List[Dict[str, Any]] = []
        self._next_id = 1

    async def initialize(self) -> None:
        logger.info("TodoService initialized")

    async def cleanup(self) -> None:
        logger.info("TodoService cleaned up")

    def register_tools(self, app) -> None:
        @app.tool(description=WRITE_TODOS_DESCRIPTION)
        async def write_todos(todos: List[Dict[str, Any]]) -> str:
            """Create or replace the todo list.

            Args:
                todos: List of todo dicts with content and status
            """
            normalized: List[Dict[str, Any]] = []
            for item in todos:
                content = item.get("content") or item.get("title") or ""
                status = item.get("status", "pending")
                if status not in {"pending", "in_progress", "completed"}:
                    status = "pending"
                tid = item.get("id") or self._next_id
                self._next_id = max(self._next_id, tid + 1)
                normalized.append({"id": tid, "content": content, "status": status})
            self._todos = normalized
            return {
                "status": "updated",
                "count": len(self._todos),
                "todos": self._todos,
            }

        @app.tool()
        async def read_todos() -> str:
            """Return a formatted representation of current todos."""
            if not self._todos:
                return "No todos currently in the list."
            status_emoji = {"pending": "⏳", "in_progress": "🔄", "completed": "✅"}
            lines = ["Current TODO List:"]
            for t in self._todos:
                emoji = status_emoji.get(t["status"], "❓")
                lines.append(f"{t['id']}. {emoji} {t['content']} ({t['status']})")
            return "\n".join(lines)

        @app.tool()
        async def update_todo(id: int, status: str = None, content: str = None) -> str:
            """Update a single todo's status and/or content."""
            for t in self._todos:
                if t["id"] == id:
                    if status and status in {"pending", "in_progress", "completed"}:
                        t["status"] = status
                    if content:
                        t["content"] = content
                    return {"status": "ok", "todo": t}
            return {"error": f"Todo id {id} not found"}

        if not self._tools_meta:
            self._tools_meta.extend([
                {
                    "name": "write_todos", 
                    "description": (write_todos.__doc__ or "").strip()
                },
                {
                    "name": "read_todos", 
                    "description": (read_todos.__doc__ or "").strip()
                },
                {
                    "name": "update_todo", 
                    "description": (update_todo.__doc__ or "").strip()
                },
            ])

    def list_tools(self):
        return self._tools_meta
