from __future__ import annotations

import asyncio
import uuid
from contextlib import suppress
from datetime import UTC, datetime

from ya.scheduler.cron import calculate_next_run
from ya.scheduler.models import CronJob, JobRun, RunStatus, make_occurrence_key
from ya.scheduler.store import SchedulerStore


class SchedulerRunner:
    def __init__(self, store: SchedulerStore) -> None:
        self._store = store

    async def run_job(self, job: CronJob) -> JobRun:
        now = datetime.now(UTC).isoformat()
        run = JobRun(
            id=uuid.uuid4().hex[:12],
            job_id=job.id,
            occurrence_key=make_occurrence_key(job.id, now),
            scheduled_at=now,
            started_at=now,
            status=RunStatus.RUNNING,
            trigger="manual",
        )
        await self._store.create_run(run)

        try:
            run.result_summary = f"Job '{job.name}' completed successfully"
            run.status = RunStatus.SUCCEEDED
        except Exception as e:
            run.status = RunStatus.FAILED
            run.error_type = type(e).__name__
            run.error_message = str(e)

        run.finished_at = datetime.now(UTC).isoformat()
        await self._store.update_run(run)

        next_run = calculate_next_run(job, after=datetime.now(UTC))
        await self._store.update_next_run(
            job.id,
            next_run.isoformat() if next_run else None,
        )

        return run


class SchedulerService:
    def __init__(
        self,
        store: SchedulerStore,
        runner: SchedulerRunner,
        tick_interval: float = 60.0,
    ) -> None:
        self._store = store
        self._runner = runner
        self._tick_interval = tick_interval
        self._running = False
        self._task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        self._running = True
        self._task = asyncio.create_task(self._tick_loop())

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task

    async def run_once(self) -> list[JobRun]:
        now = datetime.now(UTC).isoformat()
        due_jobs = await self._store.get_due_jobs(now)
        results: list[JobRun] = []
        for job in due_jobs:
            run = await self._runner.run_job(job)
            results.append(run)
        return results

    async def _tick_loop(self) -> None:
        while self._running:
            await self.run_once()
            await asyncio.sleep(self._tick_interval)
