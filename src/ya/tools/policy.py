from __future__ import annotations

from enum import StrEnum
from typing import Any

from ya.ports.tools import Tool


class RiskLevel(StrEnum):
    SAFE = "safe"
    GUARDED = "guarded"
    DANGEROUS = "dangerous"


class PermissionPolicy:
    def __init__(
        self,
        allow_risk_levels: set[RiskLevel] | None = None,
        allowlist: set[str] | None = None,
    ) -> None:
        self._allowed_risks = allow_risk_levels or {RiskLevel.SAFE}
        self._allowlist = allowlist or set()

    def can_execute(self, tool: Tool) -> bool:
        if tool.definition.name in self._allowlist:
            return True
        return RiskLevel(tool.definition.risk) in self._allowed_risks

    def authorize(
        self, tool: Tool, arguments: dict[str, Any]
    ) -> tuple[bool, str]:
        if not tool.definition.enabled:
            return False, f"Tool '{tool.definition.name}' is disabled"
        if not self.can_execute(tool):
            return False, (
                f"Tool '{tool.definition.name}' (risk: {tool.definition.risk}) "
                f"is not allowed by current policy"
            )
        return True, ""
