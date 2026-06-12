from __future__ import annotations

import asyncio
from pathlib import Path

import typer
from rich.console import Console

from ya.application.container import ServiceContainer
from ya.domain.rag.models import RAGQuery

rag_app = typer.Typer(name="rag", help="RAG knowledge base")
console = Console()


@rag_app.command("ingest")
def ingest(path: str = typer.Argument(...), namespace: str = typer.Option("personal", "--namespace", "-n")) -> None:
    async def _ingest() -> None:
        fp = Path(path)
        if not fp.exists():
            console.print(f"[red]File not found: {path}[/red]")
            return
        c = ServiceContainer()
        await c.initialize()
        try:
            chunks = await c.rag_service.ingest(str(fp), fp.read_bytes(), namespace=namespace)
            console.print(f"[green]Ingested {len(chunks)} chunks into '{namespace}'[/green]")
        finally:
            await c.close()
    asyncio.run(_ingest())


@rag_app.command("query")
def query(query: str = typer.Argument(...), namespace: str = typer.Option("personal", "--namespace", "-n"), top_k: int = typer.Option(5, "--top-k", "-k")) -> None:
    async def _query() -> None:
        c = ServiceContainer()
        await c.initialize()
        try:
            results = await c.rag_service.query(RAGQuery(query=query, namespace=namespace, top_k=top_k))
            if not results:
                console.print("[dim]No results found[/dim]")
            for i, chunk in enumerate(results):
                console.print(f"[bold]{i+1}.[/bold] {chunk.content[:120]}")
                if chunk.source:
                    console.print(f"   [dim]Source: {chunk.source}[/dim]")
        finally:
            await c.close()
    asyncio.run(_query())
