from __future__ import annotations

import asyncio
import uuid

import typer
from rich.console import Console
from rich.markdown import Markdown

from ya import __version__
from ya.application.container import ServiceContainer
from ya.config.settings import load_settings
from ya.interfaces.cli.cron_cmd import cron_app
from ya.interfaces.cli.memory_cmd import memory_app
from ya.interfaces.cli.rag_cmd import rag_app
from ya.interfaces.cli.root_cmd import root_app
from ya.interfaces.cli.skill_cmd import skill_app

app = typer.Typer(name="ya", help="YA — Linux-first personal full-stack agent", no_args_is_help=True)
app.add_typer(cron_app, name="cron")
app.add_typer(skill_app, name="skill")
app.add_typer(root_app, name="root")
app.add_typer(memory_app, name="memory")
app.add_typer(rag_app, name="rag")
console = Console()


@app.callback(invoke_without_command=True)
def main(version: bool = typer.Option(False, "--version", "-V", help="Show version")) -> None:
    if version:
        console.print(f"YA v{__version__}")
        raise typer.Exit()


@app.command()
def chat(
    session_id: str = typer.Option("", "--session", "-s"),
    model: str = typer.Option("MiniMax-M3", "--model", "-m"),
    new: bool = typer.Option(False, "--new", "-n"),
) -> None:
    async def _chat() -> None:
        settings = load_settings()
        if settings.minimax_api_key is None:
            console.print("[red]MINIMAX_API_KEY not set[/red]")
            raise typer.Exit(code=1)

        container = ServiceContainer()
        await container.initialize()
        try:
            loop = container.create_agent_loop(max_steps=10)
            if loop is None:
                console.print("[red]Failed to create agent loop[/red]")
                return
            sid = session_id if not new else uuid.uuid4().hex[:8]
            sess = await container.get_or_create_session(sid)

            console.print(f"[bold]YA Chat[/bold] (session: {sess.id})")
            console.print("[dim]/exit to quit, /new for new session[/dim]")

            while True:
                try:
                    ui = input("\nYou: ").strip()
                except (EOFError, KeyboardInterrupt):
                    break
                if not ui:
                    continue
                if ui == "/exit":
                    break
                if ui == "/new":
                    sess = await container.get_or_create_session()
                    console.print(f"[dim]New: {sess.id}[/dim]")
                    continue
                await loop.run(sess, ui)
                msgs = await container.session_store.get_messages(sess.id)
                last = [m for m in msgs if m.role.value == "assistant"]
                if last:
                    console.print(f"\nYA: {last[-1].content or ''}")
        finally:
            await container.close()
    asyncio.run(_chat())


@app.command()
def run(
    prompt: str = typer.Argument(..., help="Prompt to execute"),
    model: str = typer.Option("MiniMax-M3", "--model", "-m"),
    max_steps: int = typer.Option(10, "--max-steps"),
    session: str = typer.Option("", "--session", "-s", help="Session ID for context reuse"),
) -> None:
    async def _run() -> None:
        settings = load_settings()
        if settings.minimax_api_key is None:
            console.print("[red]MINIMAX_API_KEY not set[/red]")
            raise typer.Exit(code=1)

        container = ServiceContainer()
        await container.initialize()
        try:
            loop = container.create_agent_loop(max_steps=max_steps)
            if loop is None:
                return
            sess = await container.get_or_create_session(session, title=f"Run: {prompt[:50]}")

            console.print(f"[bold]Running:[/bold] {prompt}")
            console.print(f"[dim]Session: {sess.id}[/dim]")
            await loop.run(sess, prompt)

            msgs = await container.session_store.get_messages(sess.id)
            for msg in msgs:
                if msg.role.value == "assistant":
                    console.print(Markdown(msg.content or ""))
                elif msg.role.value == "tool":
                    console.print(f"[dim]tool:{msg.name} → {msg.content}[/dim]")
        finally:
            await container.close()
    asyncio.run(_run())


@app.command()
def doctor() -> None:
    console.print("[bold]YA Doctor[/bold]\n")
    settings = load_settings()
    paths = __import__("ya.config.paths", fromlist=["resolve_paths"]).resolve_paths(settings)

    checks: list[tuple[str, bool, str]] = [
        ("Python version", True, __import__("sys").version.split()[0]),
        ("MiniMax API key", settings.minimax_api_key is not None, "configured" if settings.minimax_api_key else "not set"),
        ("YA_HOME", paths.ya_home.exists(), str(paths.ya_home)),
        ("State DB dir", paths.state_db.parent.exists(), str(paths.state_db.parent)),
    ]
    for name, ok, detail in checks:
        icon = "[green]✓[/green]" if ok else "[yellow]⚠[/yellow]"
        console.print(f"  {icon} {name}: {detail}")
    console.print("\n[green]All checks passed![/green]" if all(c[1] for c in checks) else "\n[yellow]Some items need attention[/yellow]")


@app.command("tools")
def tools_list() -> None:
    from rich.table import Table

    from ya.tools.builtin.utc_time import UtcTimeTool
    from ya.tools.registry import ToolRegistry

    registry = ToolRegistry()
    registry.register(UtcTimeTool())

    table = Table(title="Registered Tools")
    for h in ["Name", "Source", "Risk", "Enabled", "Description"]:
        table.add_column(h, style="cyan" if h == "Name" else "")
    for name, tool in sorted(registry.list_all().items()):
        d = tool.definition
        table.add_row(name, d.source, f"[{d.risk}]{d.risk}[/{d.risk}]", "yes" if d.enabled else "no", d.description)
    console.print(table)


@app.command()
def serve(host: str = typer.Option("127.0.0.1", "--host", "-h"), port: int = typer.Option(8000, "--port", "-p")) -> None:
    import uvicorn
    console.print(f"[bold]YA Server → {host}:{port}[/bold]")
    uvicorn.run("ya.interfaces.api.app:app", host=host, port=port, reload=False)
