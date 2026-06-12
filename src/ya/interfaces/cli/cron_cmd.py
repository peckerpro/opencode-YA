from __future__ import annotations

import asyncio

import typer
from rich.console import Console
from rich.table import Table

from ya.application.cron_service import CronService

cron_app = typer.Typer(name="cron", help="Manage scheduled jobs")
console = Console()
_service = CronService()


@cron_app.command("list")
def list_jobs() -> None:
    async def _list() -> None:
        jobs = await _service.list_jobs()
        if not jobs:
            console.print("[dim]No jobs configured. Use 'ya cron add'[/dim]")
            return
        table = Table(title="Cron Jobs")
        for h in ["ID", "Name", "Type", "Schedule", "Status"]:
            table.add_column(h)
        for j in jobs:
            table.add_row(j["id"][:8], j["name"], j["type"], j["schedule"], j["status"])
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
        jid = await _service.add_job(name, schedule, job_type, prompt)
        console.print(f"[green]Job '{name}' created ({jid[:8]})[/green]")
    asyncio.run(_add())


@cron_app.command("remove")
def remove_job(job_id: str = typer.Argument(...)) -> None:
    async def _remove() -> None:
        deleted = await _service.remove_job(job_id)
        console.print("[green]Removed[/green]" if deleted else "[yellow]Not found[/yellow]")
    asyncio.run(_remove())


@cron_app.command("pause")
def pause_job(job_id: str = typer.Argument(...)) -> None:
    async def _pause() -> None:
        ok = await _service.pause_job(job_id)
        console.print("[yellow]Paused[/yellow]" if ok else "[red]Not found[/red]")
    asyncio.run(_pause())


@cron_app.command("resume")
def resume_job(job_id: str = typer.Argument(...)) -> None:
    async def _resume() -> None:
        ok = await _service.resume_job(job_id)
        console.print("[green]Resumed[/green]" if ok else "[red]Not found[/red]")
    asyncio.run(_resume())


@cron_app.command("run")
def run_job(job_id: str = typer.Argument(...)) -> None:
    async def _run() -> None:
        result = await _service.run_job(job_id)
        console.print(f"[green]Done: {result['status']}[/green]" if result else "[red]Not found[/red]")
    asyncio.run(_run())


@cron_app.command("logs")
def job_logs(job_id: str = typer.Argument(...)) -> None:
    async def _logs() -> None:
        runs = await _service.get_logs(job_id)
        if not runs:
            console.print("[dim]No runs[/dim]")
        else:
            for r in runs:
                console.print(f"  [{r['status']}] {r['scheduled_at'][:19]} {r['summary'][:60]}")
    asyncio.run(_logs())
