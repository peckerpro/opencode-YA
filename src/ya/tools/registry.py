from __future__ import annotations

import logging
from typing import Any

from ya.ports.tools import ToolDefinition, ToolResult

logger = logging.getLogger(__name__)


class ToolEntry:
    __slots__ = ("name", "definition", "handler", "check_fn")

    def __init__(self, definition: ToolDefinition, handler: Any, check_fn: Any = None) -> None:
        self.name = definition.name
        self.definition = definition
        self.handler = handler
        self.check_fn = check_fn

    def is_available(self) -> bool:
        if self.check_fn is None:
            return True
        try:
            return bool(self.check_fn())
        except Exception:
            return False


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolEntry] = {}

    def register(self, definition: ToolDefinition, handler: Any = None, check_fn: Any = None) -> None:
        if handler is None:
            handler = self
        if hasattr(definition, "definition"):
            # Old-style Tool object with .definition attribute
            tool = definition
            definition = tool.definition
            handler = tool
        if definition.name in self._tools:
            raise ValueError(f"Tool '{definition.name}' is already registered")
        self._tools[definition.name] = ToolEntry(definition, handler, check_fn)

    def get(self, name: str) -> ToolEntry | None:
        return self._tools.get(name)

    def list_definitions(self, enabled_only: bool = True) -> list[ToolDefinition]:
        defs = []
        for entry in self._tools.values():
            if enabled_only:
                if not entry.definition.enabled:
                    continue
                if not entry.is_available():
                    continue
            defs.append(entry.definition)
        return defs

    def list_all(self) -> list[ToolEntry]:
        return list(self._tools.values())

    def enable(self, name: str) -> None:
        entry = self._tools.get(name)
        if entry is None:
            raise KeyError(f"Tool '{name}' not found")
        entry.definition.enabled = True

    def disable(self, name: str) -> None:
        entry = self._tools.get(name)
        if entry is None:
            raise KeyError(f"Tool '{name}' not found")
        entry.definition.enabled = False

    async def execute(self, name: str, arguments: dict[str, Any]) -> ToolResult:
        entry = self._tools.get(name)
        if entry is None:
            return ToolResult(success=False, content="", error=f"Tool '{name}' not found")
        if not entry.definition.enabled:
            return ToolResult(success=False, content="", error=f"Tool '{name}' is disabled")
        if not entry.is_available():
            return ToolResult(success=False, content="", error=f"Tool '{name}' is not available")
        try:
            result = await entry.handler.execute(arguments)
            return result if isinstance(result, ToolResult) else ToolResult(success=True, content=str(result))
        except Exception as e:
            logger.exception("Tool %s failed", name)
            return ToolResult(success=False, content="", error=str(e))


registry = ToolRegistry()
