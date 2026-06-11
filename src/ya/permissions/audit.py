from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field


class AuditEvent(BaseModel):
    id: str = ""
    actor_agent_id: str = ""
    actor_role_id: str = ""
    capability: str = ""
    target_type: str = ""
    target_id: str = ""
    scope: str = ""
    risk: str = "safe"
    decision: str = ""
    policy_rule: str = ""
    confirmation_actor: str = ""
    started_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    finished_at: str = ""
    result_status: str = ""
    result_summary: str = ""


class AuditStore:
    def __init__(self) -> None:
        self._events: list[AuditEvent] = []

    def append(self, event: AuditEvent) -> None:
        import uuid
        event.id = uuid.uuid4().hex[:12]
        self._events.append(event)

    def query(
        self,
        capability: str | None = None,
        actor_id: str | None = None,
        limit: int = 50,
    ) -> list[AuditEvent]:
        results = self._events
        if capability:
            results = [e for e in results if e.capability == capability]
        if actor_id:
            results = [e for e in results if e.actor_agent_id == actor_id]
        return sorted(results, key=lambda e: e.started_at, reverse=True)[:limit]

    def count(self) -> int:
        return len(self._events)
