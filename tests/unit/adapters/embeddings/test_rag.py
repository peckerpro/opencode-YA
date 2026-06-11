from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from tests.unit.adapters.embeddings.fake_embedder import FakeEmbedder
from ya.adapters.parsers.text import TextParser
from ya.adapters.stores.vector import VectorStore
from ya.application.rag import RAGService
from ya.domain.rag.models import RAGQuery


class TestRAGPipeline:
    @pytest.fixture
    def vector_store(self) -> VectorStore:
        with tempfile.TemporaryDirectory(prefix="ya-rag-") as tmp:
            store = VectorStore(Path(tmp) / "vectors.db")
            store.initialize()
            yield store

    @pytest.mark.asyncio
    async def test_ingest_and_query(self, vector_store: VectorStore) -> None:
        embedder = FakeEmbedder(dimension=64)
        parser = TextParser()
        service = RAGService(embedder, vector_store, parser)

        content = (
            "Python is a high-level programming language.\n"
            "Rust is a systems programming language.\n"
            "FastAPI is a Python web framework."
        )
        chunks = await service.ingest("test.txt", content, namespace="test")
        assert len(chunks) >= 1

        results = await service.query(RAGQuery(query="Python programming", namespace="test", top_k=2))
        assert len(results) >= 1
        assert any("Python" in c.content for c in results)

    @pytest.mark.asyncio
    async def test_namespace_isolation(self, vector_store: VectorStore) -> None:
        embedder = FakeEmbedder(dimension=64)
        parser = TextParser()
        service = RAGService(embedder, vector_store, parser)

        await service.ingest("a.txt", "Python content", namespace="project-a")
        await service.ingest("b.txt", "Rust content", namespace="project-b")

        results_a = await service.query(RAGQuery(query="Python", namespace="project-a"))
        assert len(results_a) >= 1

        results_b = await service.query(RAGQuery(query="Python", namespace="project-b"))
        assert not any("Python" in c.content for c in results_b)

    @pytest.mark.asyncio
    async def test_chunk_content_hash(self, vector_store: VectorStore) -> None:
        embedder = FakeEmbedder(dimension=64)
        parser = TextParser()
        service = RAGService(embedder, vector_store, parser)

        chunks = await service.ingest("test.txt", "Hello world", namespace="test")
        assert len(chunks) >= 1
        assert chunks[0].content_hash != ""

    @pytest.mark.asyncio
    async def test_chinese_content(self, vector_store: VectorStore) -> None:
        embedder = FakeEmbedder(dimension=64)
        parser = TextParser()
        service = RAGService(embedder, vector_store, parser)

        content = "深度学习是机器学习的一个分支。\n自然语言处理是人工智能的重要领域。"
        chunks = await service.ingest("ai.txt", content, namespace="test")
        assert len(chunks) >= 1

        results = await service.query(RAGQuery(query="深度学习", namespace="test"))
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_delete_document(self, vector_store: VectorStore) -> None:
        embedder = FakeEmbedder(dimension=64)
        parser = TextParser()
        service = RAGService(embedder, vector_store, parser)

        chunks = await service.ingest("doc.txt", "Content to delete", namespace="test")
        doc_id = chunks[0].document_id

        vector_store.delete_document(doc_id)

        results = await service.query(RAGQuery(query="Content", namespace="test"))
        assert not any(c.document_id == doc_id for c in results)

    @pytest.mark.asyncio
    async def test_multiple_ingest_same_document(self, vector_store: VectorStore) -> None:
        embedder = FakeEmbedder(dimension=64)
        parser = TextParser()
        service = RAGService(embedder, vector_store, parser)

        await service.ingest("doc.txt", "Original content", namespace="test")
        await service.ingest("doc.txt", "Updated content", namespace="test")

        results = await service.query(RAGQuery(query="Updated", namespace="test"))
        assert len(results) >= 1
