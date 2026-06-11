from __future__ import annotations

import asyncio
from pathlib import Path

import typer
from rich.console import Console

from ya.adapters.parsers.text import TextParser
from ya.adapters.stores.vector import VectorStore
from ya.application.rag import RAGService
from ya.config.paths import resolve_paths
from ya.config.settings import load_settings
from ya.domain.rag.models import RAGQuery
from ya.ports.embeddings import Embedder

rag_app = typer.Typer(name="rag", help="RAG knowledge base management")
console = Console()


class _NoopEmbedder:
    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.0] * 128 for _ in texts]
    async def embed_query(self, text: str) -> list[float]:
        return [0.0] * 128


def _get_service() -> RAGService:
    settings = load_settings()
    paths = resolve_paths(settings)
    store = VectorStore(paths.rag / "vectors.db")
    store.initialize()
    parser = TextParser()
    embedder: Embedder = _NoopEmbedder()
    if settings.volcengine_api_key:
        from ya.adapters.embeddings.volcengine import VolcengineEmbedder
        embedder = VolcengineEmbedder(
            api_key=settings.volcengine_api_key.get_secret_value(),
            base_url=settings.volcengine_base_url,
            model=settings.volcengine_embedding_model,
        )
    return RAGService(embedder, store, parser)


@rag_app.command("ingest")
def ingest(
    path: str = typer.Argument(..., help="File path to ingest"),
    namespace: str = typer.Option("personal", "--namespace", "-n"),
) -> None:
    async def _ingest() -> None:
        file_path = Path(path)
        if not file_path.exists():
            console.print(f"[red]File not found: {path}[/red]")
            return
        content = file_path.read_bytes()
        service = _get_service()
        chunks = await service.ingest(str(file_path), content, namespace=namespace)
        console.print(f"[green]Ingested {len(chunks)} chunks into '{namespace}'[/green]")
    asyncio.run(_ingest())


@rag_app.command("query")
def query(
    query: str = typer.Argument(..., help="Search query"),
    namespace: str = typer.Option("personal", "--namespace", "-n"),
    top_k: int = typer.Option(5, "--top-k", "-k"),
) -> None:
    async def _query() -> None:
        service = _get_service()
        results = await service.query(RAGQuery(query=query, namespace=namespace, top_k=top_k))
        if not results:
            console.print("[dim]No results found[/dim]")
        for i, chunk in enumerate(results):
            console.print(f"[bold]{i+1}.[/bold] {chunk.content[:120]}")
            if chunk.source:
                console.print(f"   [dim]Source: {chunk.source}[/dim]")
    asyncio.run(_query())
