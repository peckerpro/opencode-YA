from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class MemoryType(StrEnum):
    DAILY = "daily"
    PROJECT = "project"
    TOPIC = "topic"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    TASK = "task"


class Memory(BaseModel):
    id: str = ""
    title: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    memory_type: MemoryType = MemoryType.SEMANTIC
    tags: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    source: str = "conversation"
    content: str = ""


class MemoryQuery(BaseModel):
    memory_type: MemoryType | None = None
    tags: list[str] | None = None
    project: str | None = None
    text_search: str | None = None
    limit: int = 20
