from __future__ import annotations

from pathlib import Path

from ya.adapters.parsers.text import TextParser
from ya.adapters.stores.vector import VectorStore
from ya.application.rag import RAGService
from ya.config.paths import resolve_paths
from ya.config.settings import load_settings
from ya.domain.rag.models import RAGQuery
from ya.ports.embeddings import Embedder


class _NoopEmbedder:
    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.0] * 128 for _ in texts]
    async def embed_query(self, text: str) -> list[float]:
        return [0.0] * 128


class RAGCLIService:
    def __init__(self, rag_path: Path | None = None) -> None:
        settings = load_settings()
        if rag_path is None:
            paths = resolve_paths(settings)
            rag_path = paths.rag
        self._store = VectorStore(rag_path / "vectors.db")
        self._store.initialize()
        parser = TextParser()
        embedder: Embedder = _NoopEmbedder()
        if settings.volcengine_api_key:
            from ya.adapters.embeddings.volcengine import VolcengineEmbedder
            embedder = VolcengineEmbedder(
                api_key=settings.volcengine_api_key.get_secret_value(),
                base_url=settings.volcengine_base_url,
                model=settings.volcengine_embedding_model,
            )
        self._service = RAGService(embedder, self._store, parser)

    async def ingest(self, path: str, namespace: str = "personal") -> int:
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(path)
        content = file_path.read_bytes()
        chunks = await self._service.ingest(str(file_path), content, namespace=namespace)
        return len(chunks)

    async def query(self, query: str, namespace: str = "personal", top_k: int = 5) -> list[dict[str, str]]:
        results = await self._service.query(RAGQuery(query=query, namespace=namespace, top_k=top_k))
        return [{"content": c.content[:200], "source": c.source} for c in results]
