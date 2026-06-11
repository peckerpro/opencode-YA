from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class RunStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


class Run(BaseModel):
    id: str = Field(default_factory=lambda: "")
    session_id: str = ""
    agent_id: str = ""
    role_id: str = ""
    status: RunStatus = RunStatus.PENDING
    started_at: str = Field(default_factory=utc_now)
    finished_at: str | None = None


class AgentEvent(BaseModel):
    id: str = Field(default_factory=lambda: "")
    run_id: str = ""
    event_type: str = ""
    payload: str = ""
    created_at: str = Field(default_factory=utc_now)
