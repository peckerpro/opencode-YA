from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class SkillSource(StrEnum):
    BUILTIN = "builtin"
    LOCAL = "local"
    COMMUNITY = "community"


class SkillStatus(StrEnum):
    ENABLED = "enabled"
    DISABLED = "disabled"


class SkillMetadata(BaseModel):
    name: str = ""
    version: str = ""
    description: str = ""
    author: str = ""
    source: SkillSource = SkillSource.LOCAL
    source_url: str = ""
    source_hash: str = ""
    license: str = ""
    required_permissions: list[str] = Field(default_factory=list)
    triggers: list[str] = Field(default_factory=list)
    status: SkillStatus = SkillStatus.DISABLED
    installed_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    path: str = ""
