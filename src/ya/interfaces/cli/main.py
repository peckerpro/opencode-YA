from __future__ import annotations

import asyncio
import sys
import uuid

import typer
from rich.console import Console
from rich.markdown import Markdown

from ya import __version__
from ya.config.paths import resolve_paths
from ya.config.settings import load_settings
from ya.interfaces.cli.cron_cmd import cron_app
from ya.interfaces.cli.memory_cmd import memory_app
from ya.interfaces.cli.rag_cmd import rag_app
from ya.interfaces.cli.root_cmd import root_app
from ya.interfaces.cli.skill_cmd import skill_app

app = typer.Typer(
    name="ya",
    help="YA — Linux-first personal full-stack agent",
    no_args_is_help=True,
)
app.add_typer(cron_app, name="cron")
app.add_typer(skill_app, name="skill")
app.add_typer(root_app, name="root")
app.add_typer(memory_app, name="memory")
app.add_typer(rag_app, name="rag")
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
    model: str = typer.Option("MiniMax-M3", "--model", "-m", help="Model to use"),
    new: bool = typer.Option(False, "--new", "-n", help="Start a new session"),
) -> None:
    async def _chat() -> None:
        settings = load_settings()
        api_key = settings.minimax_api_key
        if api_key is None:
            console.print("[red]Error: MINIMAX_API_KEY not set.[/red]")
            raise typer.Exit(code=1)

        from ya.adapters.llm.minimax import MiniMaxProvider
        from ya.adapters.stores.sqlite import SqliteSessionStore
        from ya.application.chat import AgentLoop, AgentLoopConfig
        from ya.domain.sessions.models import Session
        from ya.tools.builtin.utc_time import UtcTimeTool
        from ya.tools.policy import PermissionPolicy
        from ya.tools.registry import ToolRegistry

        paths = resolve_paths(settings)
        paths.state_db.parent.mkdir(parents=True, exist_ok=True)

        provider = MiniMaxProvider(api_key=api_key.get_secret_value(), model=model)
        registry = ToolRegistry()
        registry.register(UtcTimeTool())
        policy = PermissionPolicy()
        store = SqliteSessionStore(paths.state_db)
        await store.initialize()

        sid = session_id or uuid.uuid4().hex[:8]
        session = await store.get_session(sid)
        if session is None or new:
            session = Session(id=sid, title=f"Chat {sid}")
            await store.create_session(session)

        loop = AgentLoop(provider=provider, store=store, registry=registry, policy=policy, config=AgentLoopConfig(max_steps=10))  # type: ignore[arg-type]

        console.print(f"[bold]YA Chat[/bold] (session: {session.id})")
        console.print("[dim]Type /exit to quit, /new for new session[/dim]")

        while True:
            try:
                user_input = input("\nYou: ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if not user_input:
                continue
            if user_input == "/exit":
                break
            if user_input == "/new":
                sid = uuid.uuid4().hex[:8]
                session = Session(id=sid, title=f"Chat {sid}")
                await store.create_session(session)
                console.print(f"[dim]New session: {sid}[/dim]")
                continue

            await loop.run(session, user_input)
            messages = await store.get_messages(session.id)
            last = [m for m in messages if m.role.value == "assistant"]
            if last:
                console.print(f"\nYA: {last[-1].content or ''}")

        await store.close()

    asyncio.run(_chat())


@app.command()
def run(
    prompt: str = typer.Argument(..., help="Prompt to execute"),
    model: str = typer.Option("MiniMax-M3", "--model", "-m", help="Model to use"),
    max_steps: int = typer.Option(10, "--max-steps", help="Maximum agent steps"),
) -> None:
    async def _run() -> None:
        settings = load_settings()
        api_key = settings.minimax_api_key
        if api_key is None:
            console.print("[red]Error: MINIMAX_API_KEY not set. Run 'ya doctor' for help.[/red]")
            raise typer.Exit(code=1)

        from ya.adapters.llm.minimax import MiniMaxProvider
        from ya.adapters.stores.sqlite import SqliteSessionStore
        from ya.application.chat import AgentLoop, AgentLoopConfig
        from ya.domain.sessions.models import Session
        from ya.tools.builtin.utc_time import UtcTimeTool
        from ya.tools.policy import PermissionPolicy
        from ya.tools.registry import ToolRegistry

        paths = resolve_paths(settings)
        paths.state_db.parent.mkdir(parents=True, exist_ok=True)

        provider = MiniMaxProvider(
            api_key=api_key.get_secret_value(),
            base_url=settings.minimax_base_url,
            model=model or settings.ya_llm_model,
        )
        registry = ToolRegistry()
        registry.register(UtcTimeTool())
        policy = PermissionPolicy()
        store = SqliteSessionStore(paths.state_db)
        await store.initialize()

        session = Session(id=uuid.uuid4().hex[:12], title=f"Run: {prompt[:50]}")
        await store.create_session(session)

        loop = AgentLoop(provider=provider, store=store, registry=registry, policy=policy, config=AgentLoopConfig(max_steps=max_steps))  # type: ignore[arg-type]

        console.print(f"[bold]Running:[/bold] {prompt}")
        await loop.run(session, prompt)

        messages = await store.get_messages(session.id)
        for msg in messages:
            if msg.role.value == "assistant":
                console.print(Markdown(msg.content or ""))
            elif msg.role.value == "tool":
                console.print(f"[dim]🔧 {msg.name}: {msg.content}[/dim]")

        await store.close()

    asyncio.run(_run())


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
