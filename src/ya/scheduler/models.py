from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class JobStatus(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    DISABLED = "disabled"


class JobType(StrEnum):
    PROMPT = "prompt"
    TOOL = "tool"
    DAILY_REVIEW = "daily_review"
    TASK_CHECK = "task_check"
    CLEANUP = "cleanup"
    REPORT = "report"


class ScheduleType(StrEnum):
    CRON = "cron"
    INTERVAL = "interval"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class RunStatus(StrEnum):
    PENDING = "pending"
    CLAIMED = "claimed"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"
    BLOCKED = "blocked"


class MisfirePolicy(StrEnum):
    SKIP = "skip"
    RUN_ONCE = "run_once"
    CATCH_UP_LIMITED = "catch_up_limited"


class RetryPolicy(BaseModel):
    max_attempts: int = 3
    backoff: str = "fixed"
    initial_delay_seconds: int = 60
    max_delay_seconds: int = 3600
    retryable_error_types: list[str] = Field(default_factory=list)


class CronJob(BaseModel):
    id: str = ""
    name: str = ""
    description: str = ""
    job_type: JobType = JobType.PROMPT
    payload: dict[str, Any] = Field(default_factory=dict)
    schedule_type: ScheduleType = ScheduleType.DAILY
    schedule_value: str = ""
    timezone: str = "UTC"
    enabled: bool = True
    job_status: JobStatus = JobStatus.ACTIVE
    timeout_seconds: int = 300
    retry_policy: RetryPolicy = Field(default_factory=RetryPolicy)
    max_agent_steps: int = 10
    run_as_role: str = "session"
    scope: str = "session"
    misfire_policy: MisfirePolicy = MisfirePolicy.RUN_ONCE
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    next_run_at: str | None = None
    version: int = 1


class JobRun(BaseModel):
    id: str = ""
    job_id: str = ""
    occurrence_key: str = ""
    scheduled_at: str = ""
    started_at: str | None = None
    finished_at: str | None = None
    status: RunStatus = RunStatus.PENDING
    attempt: int = 1
    trigger: str = "scheduled"
    agent_run_id: str | None = None
    result_summary: str = ""
    error_type: str = ""
    error_message: str = ""
    log_ref: str = ""


def make_occurrence_key(job_id: str, scheduled_at: str) -> str:
    return f"{job_id}:{scheduled_at}"
