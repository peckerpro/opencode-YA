from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class TaskStatus(StrEnum):
    BACKLOG = "backlog"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    TESTING = "testing"
    BLOCKED = "blocked"
    DONE = "done"


VALID_TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
    TaskStatus.BACKLOG: {TaskStatus.READY, TaskStatus.BLOCKED},
    TaskStatus.READY: {TaskStatus.IN_PROGRESS, TaskStatus.BLOCKED},
    TaskStatus.IN_PROGRESS: {TaskStatus.REVIEW, TaskStatus.BLOCKED, TaskStatus.READY},
    TaskStatus.REVIEW: {TaskStatus.TESTING, TaskStatus.IN_PROGRESS, TaskStatus.BLOCKED},
    TaskStatus.TESTING: {TaskStatus.DONE, TaskStatus.IN_PROGRESS, TaskStatus.BLOCKED},
    TaskStatus.BLOCKED: {TaskStatus.BACKLOG, TaskStatus.READY, TaskStatus.IN_PROGRESS},
    TaskStatus.DONE: set(),
}


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


class Task(BaseModel):
    id: str
    title: str = ""
    owner: str = "unassigned"
    role: str = ""
    scope: str = ""
    status: TaskStatus = TaskStatus.BACKLOG
    blocked_reason: str = ""
    acceptance_criteria: str = ""
    created_at: str = Field(default_factory=utc_now)
    updated_at: str = Field(default_factory=utc_now)
    completed_at: str | None = None

    def transition_to(self, new_status: TaskStatus) -> None:
        allowed = VALID_TRANSITIONS.get(self.status, set())
        if new_status not in allowed:
            raise ValueError(
                f"Invalid transition: {self.status.value} -> {new_status.value}"
            )
        if new_status == TaskStatus.BLOCKED and not self.blocked_reason:
            raise ValueError("Blocked reason is required when blocking a task")
        self.status = new_status
        self.updated_at = utc_now()
        if new_status == TaskStatus.DONE:
            self.completed_at = utc_now()


class TaskEvent(BaseModel):
    task_id: str
    event_type: str
    owner: str = ""
    previous_status: str | None = None
    new_status: str | None = None
    reason: str = ""
    timestamp: str = Field(default_factory=utc_now)
