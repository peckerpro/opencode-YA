from __future__ import annotations

import asyncio

import typer
from rich.console import Console
from rich.table import Table

from ya.application.container import ServiceContainer

memory_app = typer.Typer(name="memory", help="Manage Markdown memories")
console = Console()


@memory_app.command("add")
def add_memory(title: str = typer.Option(..., "--title", "-t"), content: str = typer.Option(..., "--content", "-c"), memory_type: str = typer.Option("semantic", "--type"), tags: str = typer.Option("", "--tags")) -> None:
    async def _add() -> None:
        c = ServiceContainer()
        await c.initialize()
        try:
            mid = await c.memory_service.add(title, content, memory_type, tags)
            console.print(f"[green]Saved: {mid}[/green]")
        finally:
            await c.close()
    asyncio.run(_add())


@memory_app.command("list")
def list_memories(memory_type: str = typer.Option("", "--type", "-t"), search: str = typer.Option("", "--search", "-s"), limit: int = typer.Option(20, "--limit", "-l")) -> None:
    async def _list() -> None:
        c = ServiceContainer()
        await c.initialize()
        try:
            results = await c.memory_service.search(query=search, memory_type=memory_type, limit=limit)
            if not results:
                console.print("[dim]No memories found[/dim]")
                return
            table = Table(title="Memories")
            for h in ["ID", "Title", "Type", "Tags"]:
                table.add_column(h)
            for m in results:
                table.add_row(m["id"], m["title"][:40], m["type"], m["tags"])
            console.print(table)
        finally:
            await c.close()
    asyncio.run(_list())


@memory_app.command("show")
def show_memory(memory_id: str = typer.Argument(...)) -> None:
    async def _show() -> None:
        c = ServiceContainer()
        await c.initialize()
        try:
            mem = await c.memory_service.show(memory_id)
            if mem is None:
                console.print(f"[red]'{memory_id}' not found[/red]")
            else:
                console.print(f"[bold]{mem['title']}[/bold]")
                console.print(f"[dim]Type: {mem['type']} | Tags: {mem['tags']}[/dim]")
                console.print(mem["content"])
        finally:
            await c.close()
    asyncio.run(_show())


@memory_app.command("sync")
def sync_memories() -> None:
    async def _sync() -> None:
        c = ServiceContainer()
        await c.initialize()
        try:
            result = await c.memory_service.sync()
            console.print(f"[green]Sync: {result}[/green]")
        finally:
            await c.close()
    asyncio.run(_sync())
