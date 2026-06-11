from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class PermissionEffect(StrEnum):
    ALLOW = "allow"
    DENY = "deny"
    CONFIRM = "confirm"


class Scope(BaseModel):
    scope_type: str = "global"
    scope_id: str = ""


class Capability(BaseModel):
    name: str
    description: str = ""


class Permission(BaseModel):
    id: str = ""
    capability: str = ""
    effect: PermissionEffect = PermissionEffect.ALLOW
    scope: Scope = Field(default_factory=Scope)
    resource_pattern: str = "*"
    expires_at: str | None = None
    granted_by: str = ""
    reason: str = ""


class PermissionDecision(BaseModel):
    allowed: bool = False
    requires_confirmation: bool = False
    reason: str = ""
    matched_rule_id: str = ""
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())





CAPABILITIES = {
    "session.list": "List all sessions",
    "session.inspect": "Inspect session details",
    "session.summarize": "Summarize session content",
    "session.search": "Search across sessions",
    "session.instruction.send": "Send instruction to session",
    "session.spawn": "Spawn new session",
    "session.pause": "Pause session",
    "session.resume": "Resume session",
    "session.archive": "Archive session",
    "session.close": "Close session",
    "agent.list": "List agents",
    "system.status.read": "Read system status",
    "project.create": "Create project",
    "project.team.start": "Start project team",
    "workspace.read": "Read workspace files",
    "workspace.write": "Write workspace files",
    "task.read": "Read tasks",
    "task.transition": "Transition task status",
    "memory.read": "Read memories",
    "memory.write": "Write memories",
    "memory.sync": "Sync memories to GitHub",
    "rag.query": "Query RAG",
    "rag.reindex": "Reindex RAG",
    "cron.read": "Read cron jobs",
    "cron.manage": "Manage cron jobs",
    "tool.execute.safe": "Execute safe tools",
    "tool.execute.guarded": "Execute guarded tools",
    "tool.execute.dangerous": "Execute dangerous tools",
    "mcp.invoke": "Invoke MCP tools",
    "git.push": "Push to Git",
    "audit.read": "Read audit logs",
}
