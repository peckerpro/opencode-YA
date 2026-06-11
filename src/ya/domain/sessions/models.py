from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class SessionStatus(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"
    CLOSED = "closed"


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


class Session(BaseModel):
    id: str = Field(default_factory=lambda: "")
    title: str = ""
    status: SessionStatus = SessionStatus.ACTIVE
    default_agent_id: str = ""
    created_at: str = Field(default_factory=utc_now)
    updated_at: str = Field(default_factory=utc_now)
    last_activity_at: str = Field(default_factory=utc_now)
