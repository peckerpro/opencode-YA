from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field


class SessionSummary(BaseModel):
    session_id: str = ""
    title: str = ""
    message_count: int = 0
    last_activity: str = ""
    key_topics: list[str] = Field(default_factory=list)


class GlobalSummary(BaseModel):
    generated_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    total_sessions: int = 0
    active_sessions: int = 0
    total_memories: int = 0
    pending_tasks: int = 0
    active_cron_jobs: int = 0
    session_summaries: list[SessionSummary] = Field(default_factory=list)
    attention_items: list[str] = Field(default_factory=list)


class SummarizationService:
    def generate_global_summary(
        self,
        sessions: list[dict[str, object]],
        memory_count: int = 0,
        task_count: int = 0,
        cron_count: int = 0,
    ) -> GlobalSummary:
        active = [s for s in sessions if s.get("status") == "active"]
        summaries = [
            SessionSummary(
                session_id=str(s.get("id", "")),
                title=str(s.get("title", "")),
                message_count=int(str(s.get("message_count", 0))),
                last_activity=str(s.get("last_activity", "")),
            )
            for s in sessions
        ]

        attention: list[str] = []
        for s in sessions:
            status = str(s.get("status", ""))
            if status == "blocked":
                attention.append(f"Session {s.get('id', '')} is blocked")

        if task_count > 10:
            attention.append(f"{task_count} pending tasks need attention")
        if not active:
            attention.append("No active sessions — system is idle")

        return GlobalSummary(
            total_sessions=len(sessions),
            active_sessions=len(active),
            total_memories=memory_count,
            pending_tasks=task_count,
            active_cron_jobs=cron_count,
            session_summaries=summaries,
            attention_items=attention,
        )
