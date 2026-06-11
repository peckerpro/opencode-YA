from __future__ import annotations

import hashlib
import uuid

from ya.adapters.stores.vector import VectorStore
from ya.domain.rag.models import Chunk, RAGQuery
from ya.ports.embeddings import Embedder
from ya.ports.parsers import DocumentParser, ParsedDocument


class RAGService:
    def __init__(
        self,
        embedder: Embedder,
        vector_store: VectorStore,
        parser: DocumentParser,
    ) -> None:
        self._embedder = embedder
        self._store = vector_store
        self._parser = parser

    async def ingest(
        self,
        source: str,
        content: bytes | str,
        namespace: str = "personal",
        chunk_size: int = 500,
    ) -> list[Chunk]:
        doc = await self._parser.parse(source, content)
        document_id = uuid.uuid4().hex[:12]

        chunks = self._split_into_chunks(doc, document_id, source, namespace, chunk_size)

        texts = [c.content for c in chunks]
        embeddings = await self._embedder.embed(texts)

        for chunk, emb in zip(chunks, embeddings, strict=True):
            chunk.embedding = emb

        self._store.upsert(chunks)
        return chunks

    async def query(self, query: RAGQuery) -> list[Chunk]:
        query_embedding = await self._embedder.embed_query(query.query)
        return self._store.search(query, query_embedding)

    def _split_into_chunks(
        self,
        doc: ParsedDocument,
        document_id: str,
        source: str,
        namespace: str,
        chunk_size: int,
    ) -> list[Chunk]:
        chunks: list[Chunk] = []
        current_lines: list[str] = []
        current_len = 0

        for block in doc.blocks:
            line = block.content
            if current_len + len(line) > chunk_size and current_lines:
                chunks.append(self._make_chunk(
                    "\n".join(current_lines), document_id, source,
                    namespace, block.section, doc.parser_version,
                ))
                current_lines = []
                current_len = 0
            current_lines.append(line)
            current_len += len(line)

        if current_lines:
            chunks.append(self._make_chunk(
                "\n".join(current_lines), document_id, source,
                namespace, doc.blocks[-1].section if doc.blocks else None,
                doc.parser_version,
            ))

        return chunks

    @staticmethod
    def _make_chunk(
        content: str,
        document_id: str,
        source: str,
        namespace: str,
        section: str | None,
        parser_version: str,
    ) -> Chunk:
        return Chunk(
            id=uuid.uuid4().hex[:12],
            document_id=document_id,
            content=content,
            source=source,
            section=section,
            content_hash=hashlib.sha256(content.encode()).hexdigest()[:16],
            parser_version=parser_version,
            namespace=namespace,
        )
