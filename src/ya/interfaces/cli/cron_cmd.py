from __future__ import annotations

import asyncio
import uuid

import typer
from rich.console import Console
from rich.table import Table

from ya.config.paths import resolve_paths
from ya.config.settings import load_settings
from ya.scheduler.models import CronJob, JobStatus, JobType, ScheduleType
from ya.scheduler.store import SchedulerStore

cron_app = typer.Typer(name="cron", help="Manage scheduled jobs")
console = Console()


def _get_store() -> SchedulerStore:
    settings = load_settings()
    paths = resolve_paths(settings)
    return SchedulerStore(str(paths.cron / "scheduler.db"))


@cron_app.command("list")
def list_jobs() -> None:
    async def _list() -> None:
        store = _get_store()
        await store.initialize()
        jobs = await store.list_jobs()
        await store.close()
        if not jobs:
            console.print("[dim]No jobs configured. Use 'ya cron add'[/dim]")
            return
        table = Table(title="Cron Jobs")
        for h in ["ID", "Name", "Type", "Schedule", "Status"]:
            table.add_column(h)
        for j in jobs:
            table.add_row(j.id[:8], j.name, j.job_type.value, j.schedule_value, j.job_status.value)
        console.print(table)
    asyncio.run(_list())


@cron_app.command("add")
def add_job(
    name: str = typer.Option(..., "--name", "-n"),
    schedule: str = typer.Option("daily:09:00", "--schedule", "-s"),
    job_type: str = typer.Option("prompt", "--type", "-t"),
    prompt: str = typer.Option("", "--prompt", "-p"),
) -> None:
    async def _add() -> None:
        store = _get_store()
        await store.initialize()
        st, sv = _parse_schedule(schedule)
        jt_map = {"prompt": JobType.PROMPT, "tool": JobType.TOOL, "daily_review": JobType.DAILY_REVIEW, "task_check": JobType.TASK_CHECK, "cleanup": JobType.CLEANUP, "report": JobType.REPORT}
        job = CronJob(id=uuid.uuid4().hex[:12], name=name, job_type=jt_map.get(job_type, JobType.PROMPT), schedule_type=st, schedule_value=sv, payload={"prompt": prompt} if prompt else {})
        await store.save_job(job)
        await store.close()
        console.print(f"[green]Job '{name}' created ({job.id[:8]})[/green]")
    asyncio.run(_add())


@cron_app.command("remove")
def remove_job(job_id: str = typer.Argument(...)) -> None:
    async def _remove() -> None:
        store = _get_store()
        await store.initialize()
        deleted = await store.delete_job(job_id)
        await store.close()
        if deleted:
            console.print(f"[green]Job '{job_id[:8]}' removed[/green]")
        else:
            console.print(f"[yellow]Job '{job_id[:8]}' not found[/yellow]")
    asyncio.run(_remove())


@cron_app.command("pause")
def pause_job(job_id: str = typer.Argument(...)) -> None:
    async def _pause() -> None:
        store = _get_store()
        await store.initialize()
        job = await store.get_job(job_id)
        if job:
            job.job_status = JobStatus.PAUSED
            await store.save_job(job)
        await store.close()
        console.print(f"[yellow]Paused {job_id[:8]}[/yellow]")
    asyncio.run(_pause())


@cron_app.command("resume")
def resume_job(job_id: str = typer.Argument(...)) -> None:
    async def _resume() -> None:
        store = _get_store()
        await store.initialize()
        job = await store.get_job(job_id)
        if job:
            job.job_status = JobStatus.ACTIVE
            await store.save_job(job)
        await store.close()
        console.print(f"[green]Resumed {job_id[:8]}[/green]")
    asyncio.run(_resume())


@cron_app.command("run")
def run_job(job_id: str = typer.Argument(...)) -> None:
    async def _run() -> None:
        store = _get_store()
        await store.initialize()
        job = await store.get_job(job_id)
        if job:
            from ya.scheduler.runner import SchedulerRunner
            runner = SchedulerRunner(store)
            run_result = await runner.run_job(job)
            console.print(f"[green]Done: {run_result.status.value}[/green]")
        await store.close()
    asyncio.run(_run())


@cron_app.command("logs")
def job_logs(job_id: str = typer.Argument(...)) -> None:
    async def _logs() -> None:
        store = _get_store()
        await store.initialize()
        runs = await store.get_runs(job_id, limit=10)
        await store.close()
        if not runs:
            console.print("[dim]No runs[/dim]")
        else:
            for r in runs:
                console.print(f"  [{r.status.value}] {r.scheduled_at[:19]} {r.result_summary[:60]}")
    asyncio.run(_logs())


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
