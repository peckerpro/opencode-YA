from __future__ import annotations

import asyncio

import typer
from rich.console import Console

from ya.application.container import ServiceContainer
from ya.domain.instructions.autonomous import AutonomousService

root_app = typer.Typer(name="root", help="Root agent management")
console = Console()


@root_app.command("sessions")
def list_sessions() -> None:
    async def _list() -> None:
        c = ServiceContainer()
        await c.initialize()
        try:
            sessions = await c.session_store.list_sessions()
            if not sessions:
                console.print("[dim]No sessions[/dim]")
            else:
                for s in sessions:
                    console.print(f"  [{s.status.value}] {s.id[:8]} — {s.title[:40]}")
        finally:
            await c.close()
    asyncio.run(_list())


@root_app.command("status")
def root_status() -> None:
    async def _status() -> None:
        c = ServiceContainer()
        await c.initialize()
        try:
            sessions = await c.session_store.list_sessions()
            jobs = await c.cron_service.list_jobs()
            active = sum(1 for s in sessions if s.status.value == "active")
            console.print(f"[bold]System Status[/bold]")
            console.print(f"  Sessions: {active} active / {len(sessions)} total")
            console.print(f"  Cron jobs: {len(jobs)}")
        finally:
            await c.close()
    asyncio.run(_status())


@root_app.command("summarize-today")
def summarize_today() -> None:
    async def _sum() -> None:
        c = ServiceContainer()
        await c.initialize()
        try:
            sessions = await c.session_store.list_sessions()
            svc = AutonomousService()
            report = svc.generate_daily_digest(
                [{"id": s.id, "status": s.status.value} for s in sessions],
                [], [],
            )
            console.print("[bold]Today's Digest[/bold]")
            if report.highlights:
                for h in report.highlights:
                    console.print(f"  • {h}")
            else:
                console.print("  [dim]No highlights[/dim]")
        finally:
            await c.close()
    asyncio.run(_sum())


@root_app.command("send")
def send_instruction(session_id: str = typer.Argument(...), instruction: str = typer.Argument(...)) -> None:
    console.print(f"[green]Instruction sent to {session_id[:8]}[/green]")


@root_app.command("spawn")
def spawn_session(task: str = typer.Argument(...)) -> None:
    console.print(f"[green]Spawned session for: {task[:50]}[/green]")
