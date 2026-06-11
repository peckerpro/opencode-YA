from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ya.ports.tools import ToolDefinition


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_seconds: float = 60.0) -> None:
        self._threshold = failure_threshold
        self._recovery = recovery_seconds
        self._failures = 0
        self._last_failure_time: float = 0.0
        self._open = False

    def record_success(self) -> None:
        self._failures = 0
        self._open = False

    def record_failure(self) -> None:
        import time
        self._failures += 1
        self._last_failure_time = time.time()
        if self._failures >= self._threshold:
            self._open = True

    def is_open(self) -> bool:
        if not self._open:
            return False
        import time
        if time.time() - self._last_failure_time > self._recovery:
            self._open = False
            self._failures = 0
            return False
        return True

    @property
    def state(self) -> str:
        return "open" if self.is_open() else "closed"


class CustomTool:
    def __init__(
        self,
        definition: ToolDefinition,
        handler: Callable[..., object],
    ) -> None:
        self.definition = definition
        self._handler = handler
        self._breaker = CircuitBreaker()

    async def execute(self, arguments: dict[str, object]) -> tuple[bool, str]:
        if self._breaker.is_open():
            return False, f"Circuit breaker open for tool '{self.definition.name}'"
        try:
            result = self._handler(**arguments)
            self._breaker.record_success()
            return True, str(result)
        except Exception as e:
            self._breaker.record_failure()
            return False, str(e)


class ConfirmationStore:
    def __init__(self) -> None:
        self._confirmations: dict[str, dict[str, object]] = {}

    def request(self, tool_name: str, params: dict[str, object]) -> str:
        import uuid
        cid = uuid.uuid4().hex[:8]
        self._confirmations[cid] = {
            "tool": tool_name,
            "params": params,
            "status": "pending",
        }
        return cid

    def approve(self, confirmation_id: str) -> bool:
        if confirmation_id not in self._confirmations:
            return False
        self._confirmations[confirmation_id]["status"] = "approved"
        return True

    def deny(self, confirmation_id: str) -> bool:
        if confirmation_id not in self._confirmations:
            return False
        self._confirmations[confirmation_id]["status"] = "denied"
        return True

    def is_approved(self, confirmation_id: str) -> bool:
        c = self._confirmations.get(confirmation_id, {})
        return c.get("status") == "approved"
