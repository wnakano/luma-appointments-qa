# app/routers/base.py
from fastapi import APIRouter


class BaseRouter:
    def __init__(self, prefix: str, tags: list[str]):
        self.router = APIRouter(prefix=prefix, tags=tags)
        self.register_routes()

    def register_routes(self) -> None:
        raise NotImplementedError("Subclasses must define register_routes()")