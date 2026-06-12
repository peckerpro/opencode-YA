from __future__ import annotations

import asyncio

import typer
from rich.console import Console
from rich.table import Table

from ya.application.container import ServiceContainer

cron_app = typer.Typer(name="cron", help="Manage scheduled jobs")
console = Console()


@cron_app.command("list")
def list_jobs() -> None:
    async def _list() -> None:
        c = ServiceContainer()
        await c.initialize()
        try:
            jobs = await c.cron_service.list_jobs()
            if not jobs:
                console.print("[dim]No jobs configured[/dim]")
                return
            table = Table(title="Cron Jobs")
            for h in ["ID", "Name", "Type", "Schedule", "Status"]:
                table.add_column(h)
            for j in jobs:
                table.add_row(j["id"][:8], j["name"], j["type"], j["schedule"], j["status"])
            console.print(table)
        finally:
            await c.close()
    asyncio.run(_list())


@cron_app.command("add")
def add_job(name: str = typer.Option(..., "--name", "-n"), schedule: str = typer.Option("daily:09:00", "--schedule", "-s"), job_type: str = typer.Option("prompt", "--type", "-t"), prompt: str = typer.Option("", "--prompt", "-p")) -> None:
    async def _add() -> None:
        c = ServiceContainer()
        await c.initialize()
        try:
            jid = await c.cron_service.add_job(name, schedule, job_type, prompt)
            console.print(f"[green]Created ({jid[:8]})[/green]")
        finally:
            await c.close()
    asyncio.run(_add())


@cron_app.command("remove")
def remove_job(job_id: str = typer.Argument(...)) -> None:
    async def _remove() -> None:
        c = ServiceContainer()
        await c.initialize()
        try:
            ok = await c.cron_service.remove_job(job_id)
            console.print("[green]Removed[/green]" if ok else "[yellow]Not found[/yellow]")
        finally:
            await c.close()
    asyncio.run(_remove())


@cron_app.command("pause")
def pause_job(job_id: str = typer.Argument(...)) -> None:
    async def _p() -> None:
        c = ServiceContainer()
        await c.initialize()
        try:
            ok = await c.cron_service.pause_job(job_id)
            console.print("[yellow]Paused[/yellow]" if ok else "[red]Not found[/red]")
        finally:
            await c.close()
    asyncio.run(_p())


@cron_app.command("resume")
def resume_job(job_id: str = typer.Argument(...)) -> None:
    async def _r() -> None:
        c = ServiceContainer()
        await c.initialize()
        try:
            ok = await c.cron_service.resume_job(job_id)
            console.print("[green]Resumed[/green]" if ok else "[red]Not found[/red]")
        finally:
            await c.close()
    asyncio.run(_r())


@cron_app.command("run")
def run_job(job_id: str = typer.Argument(...)) -> None:
    async def _run() -> None:
        c = ServiceContainer()
        await c.initialize()
        try:
            r = await c.cron_service.run_job(job_id)
            console.print(f"[green]Done: {r['status']}[/green]" if r else "[red]Not found[/red]")
        finally:
            await c.close()
    asyncio.run(_run())


@cron_app.command("logs")
def job_logs(job_id: str = typer.Argument(...)) -> None:
    async def _logs() -> None:
        c = ServiceContainer()
        await c.initialize()
        try:
            runs = await c.cron_service.get_logs(job_id)
            if not runs:
                console.print("[dim]No runs[/dim]")
            else:
                for r in runs:
                    console.print(f"  [{r['status']}] {r['scheduled_at'][:19]} {r['summary'][:60]}")
        finally:
            await c.close()
    asyncio.run(_logs())
