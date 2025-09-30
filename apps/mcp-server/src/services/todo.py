import logging
from typing import Any, Dict, List, Optional
from .base import ServiceModule
from .prompts.todo import WRITE_TODOS_DESCRIPTION, TODO_USAGE_INSTRUCTIONS
from utils import Logger

logger = Logger(__name__)


class TodoService(ServiceModule):
    """Service providing planning & progress tracking tools (write_todos, read_todos).

    Uses prompt templates in prompts/todo.py for descriptions & usage guidance.
    Data Model: each todo is a dict { 'content': str, 'status': 'pending'|'in_progress'|'completed', 'id': int }
    Constraints: Exactly zero or one 'in_progress' at a time.
    """

    def __init__(self):
        self._todos: List[Dict[str, Any]] = []
        self._tools: List[Dict[str, Any]] = []
        self._next_id: int = 1

    async def initialize(self) -> None:
        logger.info("TodoService initialized (in-memory store)")

    async def cleanup(self) -> None:
        logger.info("TodoService cleanup complete")

    def register_tools(self, app) -> None:
        @app.tool(description=WRITE_TODOS_DESCRIPTION)
        async def write_todos(todos: List[Dict[str, Any]]) -> str:
            """Create or update the TODO list for task planning and tracking.

            Args:
                todos: List of todo items with content and status fields
            Returns:
                JSON summary of updated todos
            """
            normalized: List[Dict[str, Any]] = []
            seen_in_progress = False
            for item in todos:
                content = (item.get("content") or "").strip()
                status = (item.get("status") or "pending").strip()
                if status not in {"pending", "in_progress", "completed"}:
                    status = "pending"
                if status == "in_progress":
                    if seen_in_progress:
                        status = "pending"
                    else:
                        seen_in_progress = True
                existing_id = next((t["id"] for t in self._todos if t["content"] == content), None)
                todo_id = item.get("id") or existing_id or self._next_id
                if todo_id == self._next_id:
                    self._next_id += 1
                normalized.append({"id": todo_id, "content": content, "status": status})
            self._todos = normalized
            return {
                "status": "updated",
                "count": len(self._todos),
                "todos": self._todos,
            }

        @app.tool()
        async def read_todos() -> str:
            """Read the current TODO list in a formatted textual representation."""
            if not self._todos:
                return "No todos currently in the list."
            lines = ["Current TODO List:"]
            status_emoji = {"pending": "⏳", "in_progress": "🔄", "completed": "✅"}
            for i, todo in enumerate(self._todos, 1):
                emoji = status_emoji.get(todo["status"], "❓")
                lines.append(f"{i}. {emoji} {todo['content']} ({todo['status']})")
            return "\n".join(lines)

        if not self._tools:
            self._tools.extend([
                {"name": "write_todos", "description": (write_todos.__doc__ or "").strip().splitlines()[0]},
                {"name": "read_todos", "description": (read_todos.__doc__ or "").strip()},
            ])

    def list_tools(self) -> List[Dict[str, Any]]:
        return self._tools
