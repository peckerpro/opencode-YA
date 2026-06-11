from __future__ import annotations

import asyncio
import uuid

import typer
from rich.console import Console
from rich.table import Table

from ya.adapters.memory.markdown import MarkdownMemoryStore
from ya.config.paths import resolve_paths
from ya.config.settings import load_settings
from ya.domain.memory.models import Memory, MemoryQuery, MemoryType

memory_app = typer.Typer(name="memory", help="Manage Markdown memories")
console = Console()


def _get_store() -> MarkdownMemoryStore:
    settings = load_settings()
    paths = resolve_paths(settings)
    return MarkdownMemoryStore(paths.memory)


@memory_app.command("add")
def add_memory(
    title: str = typer.Option(..., "--title", "-t"),
    content: str = typer.Option(..., "--content", "-c"),
    memory_type: str = typer.Option("semantic", "--type"),
    tags: str = typer.Option("", "--tags"),
) -> None:
    async def _add() -> None:
        store = _get_store()
        mem = Memory(
            id=f"mem-{uuid.uuid4().hex[:8]}",
            title=title,
            content=content,
            memory_type=MemoryType(memory_type),
            tags=[t.strip() for t in tags.split(",") if t.strip()],
        )
        await store.save(mem)
        console.print(f"[green]Memory saved: {mem.id}[/green]")
    asyncio.run(_add())


@memory_app.command("list")
def list_memories(
    memory_type: str = typer.Option("", "--type", "-t"),
    search: str = typer.Option("", "--search", "-s"),
    limit: int = typer.Option(20, "--limit", "-l"),
) -> None:
    async def _list() -> None:
        store = _get_store()
        if search:
            results = await store.search(MemoryQuery(text_search=search, limit=limit))
        else:
            results = await store.list_all()
        if not results:
            console.print("[dim]No memories found[/dim]")
            return
        table = Table(title="Memories")
        for h in ["ID", "Title", "Type", "Tags"]:
            table.add_column(h)
        for m in results[:limit]:
            table.add_row(m.id, m.title[:40], m.memory_type.value, ",".join(m.tags[:3]))
        console.print(table)
    asyncio.run(_list())


@memory_app.command("show")
def show_memory(memory_id: str = typer.Argument(...)) -> None:
    async def _show() -> None:
        store = _get_store()
        mem = await store.get(memory_id)
        if mem is None:
            console.print(f"[red]Memory '{memory_id}' not found[/red]")
        else:
            console.print(f"[bold]{mem.title}[/bold]")
            console.print(f"[dim]Type: {mem.memory_type.value} | Tags: {', '.join(mem.tags)}[/dim]")
            console.print(mem.content)
    asyncio.run(_show())
