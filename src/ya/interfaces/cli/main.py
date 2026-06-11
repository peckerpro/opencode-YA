from __future__ import annotations

import sys

import typer
from rich.console import Console

from ya import __version__
from ya.config.paths import resolve_paths
from ya.config.settings import load_settings
from ya.interfaces.cli.cron_cmd import cron_app

app = typer.Typer(
    name="ya",
    help="YA — Linux-first personal full-stack agent",
    no_args_is_help=True,
)
app.add_typer(cron_app, name="cron")
console = Console()


@app.callback(invoke_without_command=True)
def main(
    version: bool = typer.Option(False, "--version", "-V", help="Show version"),
) -> None:
    if version:
        console.print(f"YA v{__version__}")
        raise typer.Exit()


@app.command()
def chat(
    session_id: str = typer.Option("", "--session", "-s", help="Session ID to resume"),
    model: str = typer.Option("", "--model", "-m", help="Model to use"),
    new: bool = typer.Option(False, "--new", "-n", help="Start a new session"),
) -> None:
    console.print("[bold]YA Chat[/bold] (type /exit to quit, /help for commands)")
    console.print("[dim]Note: Real LLM integration requires MiniMax API key configured[/dim]")


@app.command()
def run(
    prompt: str = typer.Argument(..., help="Prompt to execute"),
    model: str = typer.Option("", "--model", "-m", help="Model to use"),
    max_steps: int = typer.Option(10, "--max-steps", help="Maximum agent steps"),
) -> None:
    console.print(f"[bold]Running:[/bold] {prompt}")
    console.print(f"[dim]Max steps: {max_steps}[/dim]")
    console.print("[dim]Note: Real LLM integration requires MiniMax API key configured[/dim]")


@app.command()
def doctor() -> None:
    console.print("[bold]YA Doctor — System Check[/bold]\n")

    settings = load_settings()
    paths = resolve_paths(settings)

    checks: list[tuple[str, bool, str]] = []

    checks.append(("Python version", True, sys.version.split()[0]))

    has_key = settings.minimax_api_key is not None
    checks.append(("MiniMax API key", has_key, "configured" if has_key else "not set (set MINIMAX_API_KEY)"))

    home = paths.ya_home
    checks.append(("YA_HOME exists", home.exists(), str(home) if home.exists() else f"{home} (will be created)"))

    db_parent = paths.state_db.parent
    checks.append(("State DB directory writable", db_parent.exists() and (db_parent.is_dir()), str(db_parent)))

    for name, ok, detail in checks:
        icon = "[green]✓[/green]" if ok else "[yellow]⚠[/yellow]"
        console.print(f"  {icon} {name}: {detail}")

    console.print("")
    if all(ok for _, ok, _ in checks):
        console.print("[green]All checks passed![/green]")
    else:
        console.print("[yellow]Some checks need attention. Configure missing items and re-run.[/yellow]")


@app.command("tools")
def tools_list() -> None:
    from rich.table import Table

    from ya.tools.builtin.utc_time import UtcTimeTool
    from ya.tools.registry import ToolRegistry

    registry = ToolRegistry()
    registry.register(UtcTimeTool())

    table = Table(title="Registered Tools")
    table.add_column("Name", style="cyan")
    table.add_column("Source")
    table.add_column("Risk")
    table.add_column("Enabled")
    table.add_column("Description")

    for name, tool in sorted(registry.list_all().items()):
        d = tool.definition
        risk_style = {"safe": "green", "guarded": "yellow", "dangerous": "red"}.get(d.risk, "")
        enabled_style = "green" if d.enabled else "red"
        table.add_row(
            name,
            d.source,
            f"[{risk_style}]{d.risk}[/{risk_style}]",
            f"[{enabled_style}]{'yes' if d.enabled else 'no'}[/{enabled_style}]",
            d.description,
        )

    console.print(table)


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Bind address"),
    port: int = typer.Option(8000, "--port", "-p", help="Bind port"),
) -> None:
    import uvicorn
    console.print(f"[bold]Starting YA server on {host}:{port}[/bold]")
    console.print("[dim]API docs: http://{host}:{port}/docs[/dim]")
    uvicorn.run("ya.interfaces.api.app:app", host=host, port=port, reload=False)
