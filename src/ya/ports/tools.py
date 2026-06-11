from __future__ import annotations

from abc import abstractmethod
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel


class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters: dict[str, Any]
    source: str = "builtin"
    risk: str = "safe"
    enabled: bool = True


class ToolResult(BaseModel):
    success: bool
    content: str
    error: str | None = None


@runtime_checkable
class Tool(Protocol):
    definition: ToolDefinition

    @abstractmethod
    async def execute(self, arguments: dict[str, Any]) -> ToolResult: ...
