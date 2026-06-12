from __future__ import annotations

import uuid

from ya.scheduler.models import CronJob, JobStatus, JobType, ScheduleType
from ya.scheduler.store import SchedulerStore


class CronService:
    def __init__(self, store: SchedulerStore) -> None:
        self._store = store

    async def initialize(self) -> None:
        await self._store.initialize()

    async def close(self) -> None:
        await self._store.close()

    async def list_jobs(self) -> list[dict[str, str]]:
        jobs = await self._store.list_jobs()
        return [{"id": j.id, "name": j.name, "type": j.job_type.value, "schedule": j.schedule_value, "status": j.job_status.value} for j in jobs]

    async def add_job(self, name: str, schedule: str = "daily:09:00", job_type: str = "prompt", prompt: str = "") -> str:
        st, sv = _parse_schedule(schedule)
        jt_map = {"prompt": JobType.PROMPT, "tool": JobType.TOOL, "daily_review": JobType.DAILY_REVIEW, "task_check": JobType.TASK_CHECK, "cleanup": JobType.CLEANUP, "report": JobType.REPORT}
        job = CronJob(id=uuid.uuid4().hex[:12], name=name, job_type=jt_map.get(job_type, JobType.PROMPT), schedule_type=st, schedule_value=sv, payload={"prompt": prompt} if prompt else {})
        await self._store.save_job(job)
        return job.id

    async def remove_job(self, job_id: str) -> bool:
        return await self._store.delete_job(job_id)

    async def pause_job(self, job_id: str) -> bool:
        job = await self._store.get_job(job_id)
        if not job:
            return False
        job.job_status = JobStatus.PAUSED
        await self._store.save_job(job)
        return True

    async def resume_job(self, job_id: str) -> bool:
        job = await self._store.get_job(job_id)
        if not job:
            return False
        job.job_status = JobStatus.ACTIVE
        await self._store.save_job(job)
        return True

    async def run_job(self, job_id: str) -> dict[str, str] | None:
        job = await self._store.get_job(job_id)
        if job is None:
            return None
        from ya.scheduler.runner import SchedulerRunner
        runner = SchedulerRunner(self._store)
        run_result = await runner.run_job(job)
        return {"status": run_result.status.value, "job_id": job_id}

    async def get_logs(self, job_id: str, limit: int = 10) -> list[dict[str, str]]:
        runs = await self._store.get_runs(job_id, limit=limit)
        return [{"status": r.status.value, "scheduled_at": r.scheduled_at, "summary": r.result_summary} for r in runs]


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
