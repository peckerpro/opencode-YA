from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ya.ports.tools import Tool, ToolDefinition


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        name = tool.definition.name
        if name in self._tools:
            raise ValueError(f"Tool '{name}' is already registered")
        if not tool.definition.parameters:
            raise ValueError(f"Tool '{name}' has no parameter schema")
        self._tools[name] = tool

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def list_definitions(self, enabled_only: bool = True) -> list[ToolDefinition]:
        defs = [t.definition for t in self._tools.values()]
        if enabled_only:
            defs = [d for d in defs if d.enabled]
        return defs

    def list_all(self) -> Mapping[str, Tool]:
        return dict(self._tools)

    def disable(self, name: str) -> None:
        tool = self._tools.get(name)
        if tool is None:
            raise KeyError(f"Tool '{name}' not found")
        tool.definition.enabled = False

    def enable(self, name: str) -> None:
        tool = self._tools.get(name)
        if tool is None:
            raise KeyError(f"Tool '{name}' not found")
        tool.definition.enabled = True

    async def execute(self, name: str, arguments: dict[str, Any]) -> Any:
        tool = self._tools.get(name)
        if tool is None:
            raise KeyError(f"Tool '{name}' not found")
        if not tool.definition.enabled:
            raise PermissionError(f"Tool '{name}' is disabled")
        return await tool.execute(arguments)
