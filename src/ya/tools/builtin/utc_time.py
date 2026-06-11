from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from ya.ports.tools import ToolDefinition, ToolResult


class UtcTimeTool:
    def __init__(self) -> None:
        self.definition = ToolDefinition(
            name="utc_time",
            description="Return the current UTC time in ISO 8601 format",
            parameters={
                "type": "object",
                "properties": {},
                "required": [],
            },
            source="builtin",
            risk="safe",
            enabled=True,
        )

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        now = datetime.now(UTC).isoformat()
        return ToolResult(success=True, content=now)
