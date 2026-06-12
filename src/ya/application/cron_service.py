from __future__ import annotations

import uuid
from pathlib import Path

from ya.config.paths import resolve_paths
from ya.config.settings import load_settings
from ya.scheduler.models import CronJob, JobStatus, JobType, ScheduleType
from ya.scheduler.store import SchedulerStore


class CronService:
    def __init__(self, db_path: Path | None = None) -> None:
        if db_path is None:
            settings = load_settings()
            paths = resolve_paths(settings)
            db_path = paths.cron / "scheduler.db"
        self._db_path = str(db_path)

    async def _get_store(self) -> SchedulerStore:
        store = SchedulerStore(self._db_path)
        await store.initialize()
        return store

    async def list_jobs(self) -> list[dict[str, str]]:
        store = await self._get_store()
        try:
            jobs = await store.list_jobs()
            return [{"id": j.id, "name": j.name, "type": j.job_type.value, "schedule": j.schedule_value, "status": j.job_status.value} for j in jobs]
        finally:
            await store.close()

    async def add_job(self, name: str, schedule: str = "daily:09:00", job_type: str = "prompt", prompt: str = "") -> str:
        st, sv = _parse_schedule(schedule)
        jt_map = {"prompt": JobType.PROMPT, "tool": JobType.TOOL, "daily_review": JobType.DAILY_REVIEW, "task_check": JobType.TASK_CHECK, "cleanup": JobType.CLEANUP, "report": JobType.REPORT}
        job = CronJob(id=uuid.uuid4().hex[:12], name=name, job_type=jt_map.get(job_type, JobType.PROMPT), schedule_type=st, schedule_value=sv, payload={"prompt": prompt} if prompt else {})
        store = await self._get_store()
        try:
            await store.save_job(job)
            return job.id
        finally:
            await store.close()

    async def remove_job(self, job_id: str) -> bool:
        store = await self._get_store()
        try:
            return await store.delete_job(job_id)
        finally:
            await store.close()

    async def pause_job(self, job_id: str) -> bool:
        store = await self._get_store()
        try:
            job = await store.get_job(job_id)
            if job:
                job.job_status = JobStatus.PAUSED
                await store.save_job(job)
                return True
            return False
        finally:
            await store.close()

    async def resume_job(self, job_id: str) -> bool:
        store = await self._get_store()
        try:
            job = await store.get_job(job_id)
            if job:
                job.job_status = JobStatus.ACTIVE
                await store.save_job(job)
                return True
            return False
        finally:
            await store.close()

    async def run_job(self, job_id: str) -> dict[str, str] | None:
        store = await self._get_store()
        try:
            job = await store.get_job(job_id)
            if job is None:
                return None
            from ya.scheduler.runner import SchedulerRunner
            runner = SchedulerRunner(store)
            run_result = await runner.run_job(job)
            return {"status": run_result.status.value, "job_id": job_id}
        finally:
            await store.close()

    async def get_logs(self, job_id: str, limit: int = 10) -> list[dict[str, str]]:
        store = await self._get_store()
        try:
            runs = await store.get_runs(job_id, limit=limit)
            return [{"status": r.status.value, "scheduled_at": r.scheduled_at, "summary": r.result_summary} for r in runs]
        finally:
            await store.close()


def _parse_schedule(schedule: str) -> tuple[ScheduleType, str]:
    if schedule.startswith("daily:"):
        return ScheduleType.DAILY, schedule[6:]
    if schedule.startswith("weekly:"):
        return ScheduleType.WEEKLY, schedule[7:]
    if schedule.startswith("monthly:"):
        return ScheduleType.MONTHLY, schedule[8:]
    if schedule.startswith("interval:"):
        return ScheduleType.INTERVAL, schedule[9:]
    if " " in schedule and len(schedule.split()) == 5:
        return ScheduleType.CRON, schedule
    return ScheduleType.DAILY, "09:00"
