from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from ya.scheduler.models import CronJob, JobType, ScheduleType
from ya.scheduler.runner import SchedulerRunner
from ya.scheduler.store import SchedulerStore


class TestSchedulerRunner:
    @pytest.fixture
    async def store(self) -> SchedulerStore:
        with tempfile.TemporaryDirectory(prefix="ya-sched-run-") as tmp:
            s = SchedulerStore(str(Path(tmp) / "scheduler.db"))
            await s.initialize()
            yield s
            await s.close()

    @pytest.mark.asyncio
    async def test_run_job_success(self, store: SchedulerStore) -> None:
        job = CronJob(
            id="j1", name="Test Job", job_type=JobType.DAILY_REVIEW,
            schedule_type=ScheduleType.DAILY, schedule_value="09:00",
        )
        await store.save_job(job)

        runner = SchedulerRunner(store)
        run = await runner.run_job(job)

        assert run.status.value == "succeeded"
        assert "completed" in run.result_summary

        updated_job = await store.get_job("j1")
        assert updated_job is not None
        assert updated_job.next_run_at is not None

    @pytest.mark.asyncio
    async def test_run_job_updates_next_run(self, store: SchedulerStore) -> None:
        job = CronJob(
            id="j1", name="Daily", job_type=JobType.DAILY_REVIEW,
            schedule_type=ScheduleType.DAILY, schedule_value="09:00",
        )
        await store.save_job(job)

        runner = SchedulerRunner(store)
        await runner.run_job(job)

        updated = await store.get_job("j1")
        assert updated is not None
        assert updated.next_run_at is not None

    @pytest.mark.asyncio
    async def test_run_creates_job_run_record(self, store: SchedulerStore) -> None:
        job = CronJob(id="j1", name="Daily", job_type=JobType.DAILY_REVIEW)
        await store.save_job(job)

        runner = SchedulerRunner(store)
        await runner.run_job(job)

        runs = await store.get_runs("j1")
        assert len(runs) == 1
        assert runs[0].status.value == "succeeded"
