from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from ya.skills.registry import SkillRegistry

skill_app = typer.Typer(name="skill", help="Manage skills")
console = Console()


def _get_registry() -> SkillRegistry:
    r = SkillRegistry(Path.home() / ".ya" / "skills")
    r.initialize()
    return r


@skill_app.command("list")
def list_skills() -> None:
    skills = _get_registry().list_all()
    if not skills:
        console.print("[dim]No skills installed[/dim]")
        return
    table = Table(title="Installed Skills")
    for h in ["Name", "Version", "Source", "Status"]:
        table.add_column(h)
    for s in skills:
        table.add_row(s.name, s.version, s.source.value, s.status.value)
    console.print(table)


@skill_app.command("install")
def install_skill(path: str = typer.Argument(...)) -> None:
    try:
        meta = _get_registry().install_local(Path(path))
        console.print(f"[green]Installed: {meta.name} v{meta.version}[/green]")
    except ValueError as e:
        console.print(f"[red]{e}[/red]")


@skill_app.command("enable")
def enable_skill(name: str = typer.Argument(...)) -> None:
    try:
        _get_registry().enable(name)
        console.print(f"[green]Enabled: {name}[/green]")
    except KeyError:
        console.print(f"[red]Skill '{name}' not found[/red]")


@skill_app.command("disable")
def disable_skill(name: str = typer.Argument(...)) -> None:
    try:
        _get_registry().disable(name)
        console.print(f"[yellow]Disabled: {name}[/yellow]")
    except KeyError:
        console.print(f"[red]Skill '{name}' not found[/red]")


@skill_app.command("remove")
def remove_skill(name: str = typer.Argument(...)) -> None:
    try:
        _get_registry().remove(name)
        console.print(f"[green]Removed: {name}[/green]")
    except KeyError:
        console.print(f"[red]Skill '{name}' not found[/red]")
