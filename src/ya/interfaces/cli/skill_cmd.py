from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

skill_app = typer.Typer(name="skill", help="Manage skills")
console = Console()


@skill_app.command("list")
def list_skills() -> None:
    table = Table(title="Installed Skills")
    table.add_column("Name")
    table.add_column("Version")
    table.add_column("Source")
    table.add_column("Status")

    console.print("[dim]No skills installed. Use 'ya skill install' to add one.[/dim]")


@skill_app.command("install")
def install_skill(
    path: str = typer.Argument(..., help="Path to skill directory or SKILL.md"),
) -> None:
    console.print(f"[green]Skill installed from: {path}[/green]")


@skill_app.command("enable")
def enable_skill(name: str = typer.Argument(..., help="Skill name")) -> None:
    console.print(f"[green]Skill '{name}' enabled[/green]")


@skill_app.command("disable")
def disable_skill(name: str = typer.Argument(..., help="Skill name")) -> None:
    console.print(f"[yellow]Skill '{name}' disabled[/yellow]")


@skill_app.command("remove")
def remove_skill(name: str = typer.Argument(..., help="Skill name")) -> None:
    console.print(f"[yellow]Skill '{name}' removed[/yellow]")
