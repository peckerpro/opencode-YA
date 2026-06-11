from __future__ import annotations

from ya.scheduler.models import CronJob, JobType, ScheduleType
from ya.scheduler.runner import SchedulerRunner
from ya.scheduler.store import SchedulerStore


class SchedulerIntegration:
    def __init__(self, store: SchedulerStore, runner: SchedulerRunner) -> None:
        self._store = store
        self._runner = runner

    async def create_memory_sync_job(self, schedule: str = "daily:03:00") -> CronJob:
        job = CronJob(
            id="v3-memory-sync",
            name="Memory Sync",
            job_type=JobType.DAILY_REVIEW,
            schedule_type=ScheduleType.DAILY,
            schedule_value=schedule,
            description="Auto-sync Markdown memories",
        )
        await self._store.save_job(job)
        return job

    async def create_rag_reindex_job(self, schedule: str = "weekly:mon:04:00") -> CronJob:
        job = CronJob(
            id="v3-rag-reindex",
            name="RAG Re-index",
            job_type=JobType.REPORT,
            schedule_type=ScheduleType.WEEKLY,
            schedule_value=schedule,
            description="Rebuild RAG vector index",
        )
        await self._store.save_job(job)
        return job

    async def create_task_check_job(self, schedule: str = "daily:09:00") -> CronJob:
        job = CronJob(
            id="v3-task-check",
            name="Task Board Check",
            job_type=JobType.TASK_CHECK,
            schedule_type=ScheduleType.DAILY,
            schedule_value=schedule,
            description="Check task board for stale/blocked tasks",
        )
        await self._store.save_job(job)
        return job


class CircuitBreakerExecutor:
    def __init__(self, failure_threshold: int = 5, recovery_seconds: float = 300.0) -> None:
        self._threshold = failure_threshold
        self._recovery = recovery_seconds
        self._failure_counts: dict[str, int] = {}
        self._last_failures: dict[str, float] = {}
        self._open_breakers: set[str] = set()

    def is_open(self, job_id: str) -> bool:
        if job_id not in self._open_breakers:
            return False
        import time
        last = self._last_failures.get(job_id, 0)
        if time.time() - last > self._recovery:
            self._open_breakers.discard(job_id)
            self._failure_counts[job_id] = 0
            return False
        return True

    def record_failure(self, job_id: str) -> None:
        import time
        self._failure_counts[job_id] = self._failure_counts.get(job_id, 0) + 1
        self._last_failures[job_id] = time.time()
        if self._failure_counts[job_id] >= self._threshold:
            self._open_breakers.add(job_id)

    def record_success(self, job_id: str) -> None:
        self._failure_counts[job_id] = 0
        self._open_breakers.discard(job_id)
