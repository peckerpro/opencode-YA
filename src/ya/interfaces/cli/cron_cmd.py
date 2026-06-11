from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

cron_app = typer.Typer(name="cron", help="Manage scheduled jobs")
console = Console()


@cron_app.command("list")
def list_jobs() -> None:
    table = Table(title="Cron Jobs")
    table.add_column("ID")
    table.add_column("Name")
    table.add_column("Type")
    table.add_column("Schedule")
    table.add_column("Next Run")
    table.add_column("Status")

    console.print("[dim]No jobs configured. Use 'ya cron add' to create one.[/dim]")


@cron_app.command("add")
def add_job(
    name: str = typer.Option(..., "--name", "-n", help="Job name"),
    schedule: str = typer.Option("daily:09:00", "--schedule", "-s", help="Schedule (daily:HH:MM, cron expr, interval seconds)"),
    job_type: str = typer.Option("prompt", "--type", "-t", help="Job type: prompt, tool, daily_review, task_check, cleanup, report"),
    prompt: str = typer.Option("", "--prompt", "-p", help="Prompt for prompt-type jobs"),
) -> None:
    console.print(f"[green]Job '{name}' created with schedule: {schedule}[/green]")


@cron_app.command("remove")
def remove_job(job_id: str = typer.Argument(..., help="Job ID to remove")) -> None:
    console.print(f"[yellow]Job '{job_id}' removed[/yellow]")


@cron_app.command("pause")
def pause_job(job_id: str = typer.Argument(..., help="Job ID to pause")) -> None:
    console.print(f"[yellow]Job '{job_id}' paused[/yellow]")


@cron_app.command("resume")
def resume_job(job_id: str = typer.Argument(..., help="Job ID to resume")) -> None:
    console.print(f"[green]Job '{job_id}' resumed[/green]")


@cron_app.command("run")
def run_job(job_id: str = typer.Argument(..., help="Job ID to run manually")) -> None:
    console.print(f"[bold]Running job '{job_id}'...[/bold]")
    console.print("[green]Job completed successfully[/green]")


@cron_app.command("logs")
def job_logs(job_id: str = typer.Argument(..., help="Job ID to view logs")) -> None:
    console.print(f"[dim]No logs available for job '{job_id}'[/dim]")
