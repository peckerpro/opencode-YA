from __future__ import annotations

import typer
from rich.console import Console

root_app = typer.Typer(name="root", help="Root agent management commands")
console = Console()


@root_app.command("sessions")
def list_sessions() -> None:
    console.print("[bold]Active Sessions[/bold]")
    console.print("[dim]No active sessions. Start a chat to create one.[/dim]")


@root_app.command("status")
def root_status() -> None:
    console.print("[bold]YA System Status[/bold]")
    console.print("  Active sessions: 0")
    console.print("  Total memories: 0")
    console.print("  Active cron jobs: 0")


@root_app.command("send")
def send_instruction(
    session_id: str = typer.Argument(..., help="Target session ID"),
    instruction: str = typer.Argument(..., help="Instruction to send"),
) -> None:
    console.print(f"[green]Instruction sent to session '{session_id}'[/green]")


@root_app.command("spawn")
def spawn_session(task: str = typer.Argument(..., help="Task description")) -> None:
    console.print(f"[green]Session spawned for task: {task}[/green]")


@root_app.command("summarize-today")
def summarize_today() -> None:
    console.print("[bold]Today's Digest[/bold]")
    from ya.domain.instructions.autonomous import AutonomousService
    svc = AutonomousService()
    report = svc.generate_daily_digest([], [], [])
    console.print(f"  Active sessions: {report.active_sessions}")
    console.print(f"  New memories: {report.new_memories}")
    if report.highlights:
        console.print("\n[bold]Highlights:[/bold]")
        for h in report.highlights:
            console.print(f"  • {h}")
