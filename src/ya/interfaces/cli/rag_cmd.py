from __future__ import annotations

import asyncio

import typer
from rich.console import Console

from ya.application.rag_cli_service import RAGCLIService

rag_app = typer.Typer(name="rag", help="RAG knowledge base management")
console = Console()
_service = RAGCLIService()


@rag_app.command("ingest")
def ingest(
    path: str = typer.Argument(..., help="File path to ingest"),
    namespace: str = typer.Option("personal", "--namespace", "-n"),
) -> None:
    async def _ingest() -> None:
        try:
            count = await _service.ingest(path, namespace)
            console.print(f"[green]Ingested {count} chunks into '{namespace}'[/green]")
        except FileNotFoundError:
            console.print(f"[red]File not found: {path}[/red]")
    asyncio.run(_ingest())


@rag_app.command("query")
def query(
    query: str = typer.Argument(..., help="Search query"),
    namespace: str = typer.Option("personal", "--namespace", "-n"),
    top_k: int = typer.Option(5, "--top-k", "-k"),
) -> None:
    async def _query() -> None:
        results = await _service.query(query, namespace, top_k)
        if not results:
            console.print("[dim]No results found[/dim]")
        for i, chunk in enumerate(results):
            console.print(f"[bold]{i+1}.[/bold] {chunk['content'][:120]}")
            if chunk["source"]:
                console.print(f"   [dim]Source: {chunk['source']}[/dim]")
    asyncio.run(_query())
