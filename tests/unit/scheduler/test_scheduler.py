from __future__ import annotations

import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from ya.scheduler.cron import calculate_next_run
from ya.scheduler.models import (
    CronJob,
    JobRun,
    JobStatus,
    JobType,
    RunStatus,
    ScheduleType,
    make_occurrence_key,
)
from ya.scheduler.store import SchedulerStore


class TestCronCalculation:
    def test_daily_schedule(self) -> None:
        job = CronJob(
            id="j1", schedule_type=ScheduleType.DAILY,
            schedule_value="09:00", enabled=True,
        )
        base = datetime(2026, 6, 11, 8, 0, tzinfo=UTC)
        next_run = calculate_next_run(job, after=base)
        assert next_run is not None
        assert next_run.hour == 9
        assert next_run.minute == 0

    def test_daily_already_passed(self) -> None:
        job = CronJob(
            id="j1", schedule_type=ScheduleType.DAILY,
            schedule_value="08:00", enabled=True,
        )
        base = datetime(2026, 6, 11, 9, 0, tzinfo=UTC)
        next_run = calculate_next_run(job, after=base)
        assert next_run is not None
        assert next_run.day == 12

    def test_cron_expression(self) -> None:
        job = CronJob(
            id="j1", schedule_type=ScheduleType.CRON,
            schedule_value="0 8 * * *", enabled=True,
        )
        base = datetime(2026, 6, 11, 7, 0, tzinfo=UTC)
        next_run = calculate_next_run(job, after=base)
        assert next_run is not None
        assert next_run.hour == 8

    def test_interval_schedule(self) -> None:
        job = CronJob(
            id="j1", schedule_type=ScheduleType.INTERVAL,
            schedule_value="3600", enabled=True,
        )
        base = datetime(2026, 6, 11, 8, 0, tzinfo=UTC)
        next_run = calculate_next_run(job, after=base)
        assert next_run is not None
        assert next_run == base + timedelta(seconds=3600)

    def test_weekly_schedule(self) -> None:
        job = CronJob(
            id="j1", schedule_type=ScheduleType.WEEKLY,
            schedule_value="mon:09:00", enabled=True,
        )
        base = datetime(2026, 6, 10, 8, 0, tzinfo=UTC)
        next_run = calculate_next_run(job, after=base)
        assert next_run is not None

    def test_disabled_job_returns_none(self) -> None:
        job = CronJob(
            id="j1", schedule_type=ScheduleType.DAILY,
            schedule_value="09:00", enabled=False,
        )
        assert calculate_next_run(job) is None

    def test_paused_job_returns_none(self) -> None:
        job = CronJob(
            id="j1", schedule_type=ScheduleType.DAILY,
            schedule_value="09:00", job_status=JobStatus.PAUSED,
        )
        assert calculate_next_run(job) is None


class TestSchedulerStore:
    @pytest.fixture
    async def store(self) -> SchedulerStore:
        with tempfile.TemporaryDirectory(prefix="ya-sched-") as tmp:
            s = SchedulerStore(str(Path(tmp) / "scheduler.db"))
            await s.initialize()
            yield s
            await s.close()

    @pytest.mark.asyncio
    async def test_save_and_get_job(self, store: SchedulerStore) -> None:
        job = CronJob(id="j1", name="Daily Review", job_type=JobType.DAILY_REVIEW)
        await store.save_job(job)

        retrieved = await store.get_job("j1")
        assert retrieved is not None
        assert retrieved.name == "Daily Review"

    @pytest.mark.asyncio
    async def test_list_jobs(self, store: SchedulerStore) -> None:
        await store.save_job(CronJob(id="j1"))
        await store.save_job(CronJob(id="j2"))
        jobs = await store.list_jobs()
        assert len(jobs) == 2

    @pytest.mark.asyncio
    async def test_delete_job(self, store: SchedulerStore) -> None:
        await store.save_job(CronJob(id="j1"))
        await store.delete_job("j1")
        assert await store.get_job("j1") is None

    @pytest.mark.asyncio
    async def test_create_and_get_runs(self, store: SchedulerStore) -> None:
        await store.save_job(CronJob(id="j1"))
        run = JobRun(
            id="r1", job_id="j1",
            occurrence_key=make_occurrence_key("j1", "2026-01-01T00:00:00Z"),
            scheduled_at="2026-01-01T00:00:00Z",
        )
        await store.create_run(run)

        runs = await store.get_runs("j1")
        assert len(runs) == 1
        assert runs[0].status == RunStatus.PENDING

    @pytest.mark.asyncio
    async def test_update_run_status(self, store: SchedulerStore) -> None:
        await store.save_job(CronJob(id="j1"))
        run = JobRun(
            id="r1", job_id="j1",
            occurrence_key=make_occurrence_key("j1", "2026-01-01T00:00:00Z"),
            scheduled_at="2026-01-01T00:00:00Z",
        )
        await store.create_run(run)

        run.status = RunStatus.SUCCEEDED
        await store.update_run(run)

        runs = await store.get_runs("j1")
        assert runs[0].status == RunStatus.SUCCEEDED

    @pytest.mark.asyncio
    async def test_unique_occurrence_key(self, store: SchedulerStore) -> None:
        await store.save_job(CronJob(id="j1"))
        run1 = JobRun(
            id="r1", job_id="j1",
            occurrence_key=make_occurrence_key("j1", "2026-01-01T00:00:00Z"),
            scheduled_at="2026-01-01T00:00:00Z",
        )
        await store.create_run(run1)

        run2 = JobRun(
            id="r2", job_id="j1",
            occurrence_key=make_occurrence_key("j1", "2026-01-01T00:00:00Z"),
            scheduled_at="2026-01-01T00:00:00Z",
        )
        with pytest.raises(Exception):  # noqa: B017
            await store.create_run(run2)

    @pytest.mark.asyncio
    async def test_get_due_jobs(self, store: SchedulerStore) -> None:
        past = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
        future = (datetime.now(UTC) + timedelta(hours=1)).isoformat()

        await store.save_job(CronJob(
            id="j1", next_run_at=past, enabled=True,
        ))
        await store.save_job(CronJob(
            id="j2", next_run_at=future, enabled=True,
        ))

        due = await store.get_due_jobs(datetime.now(UTC).isoformat())
        assert len(due) == 1
        assert due[0].id == "j1"
