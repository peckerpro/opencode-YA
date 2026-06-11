from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class InstructionStatus(StrEnum):
    QUEUED = "queued"
    ACCEPTED = "accepted"
    RUNNING = "running"
    COMPLETED = "completed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class Instruction(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    source_agent_id: str = ""
    source_session_id: str = ""
    target_session_id: str = ""
    content: str = ""
    status: InstructionStatus = InstructionStatus.QUEUED
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    completed_at: str | None = None
    result_summary: str = ""


class SessionLifecycle:
    @staticmethod
    def can_pause(status: str) -> bool:
        return status in ("active",)

    @staticmethod
    def can_resume(status: str) -> bool:
        return status == "paused"

    @staticmethod
    def can_archive(status: str) -> bool:
        return status in ("active", "paused")

    @staticmethod
    def can_close(status: str) -> bool:
        return status in ("active", "paused", "archived")
