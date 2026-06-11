from __future__ import annotations

import sqlite3
from pathlib import Path

import numpy as np

from ya.domain.rag.models import Chunk, RAGQuery


class VectorStore:
    def __init__(self, db_path: Path) -> None:
        self._db_path = str(db_path)

    def initialize(self) -> None:
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chunks (
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    source TEXT NOT NULL DEFAULT '',
                    section TEXT,
                    content_hash TEXT NOT NULL DEFAULT '',
                    parser_version TEXT NOT NULL DEFAULT '',
                    namespace TEXT NOT NULL DEFAULT 'personal',
                    embedding BLOB
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_chunks_doc ON chunks(document_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_chunks_ns ON chunks(namespace)")
            conn.commit()

    def upsert(self, chunks: list[Chunk]) -> None:
        with sqlite3.connect(self._db_path) as conn:
            for chunk in chunks:
                emb_bytes = (
                    np.array(chunk.embedding, dtype=np.float32).tobytes()
                    if chunk.embedding else None
                )
                conn.execute(
                    """INSERT OR REPLACE INTO chunks
                    (id, document_id, content, source, section, content_hash,
                     parser_version, namespace, embedding)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        chunk.id, chunk.document_id, chunk.content,
                        chunk.source, chunk.section, chunk.content_hash,
                        chunk.parser_version, chunk.namespace, emb_bytes,
                    ),
                )
            conn.commit()

    def search(self, query: RAGQuery, query_embedding: list[float]) -> list[Chunk]:
        query_vec = np.array(query_embedding, dtype=np.float32)
        results: list[tuple[float, Chunk]] = []

        with sqlite3.connect(self._db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM chunks WHERE namespace = ?",
                (query.namespace,),
            ).fetchall()

            for row in rows:
                if row[8] is None:
                    continue
                emb = np.frombuffer(row[8], dtype=np.float32)
                similarity = float(np.dot(query_vec, emb) / (
                    np.linalg.norm(query_vec) * np.linalg.norm(emb) + 1e-10
                ))
                chunk = Chunk(
                    id=row[0], document_id=row[1], content=row[2],
                    source=row[3], section=row[4], content_hash=row[5],
                    parser_version=row[6], namespace=row[7],
                )
                results.append((similarity, chunk))

        results.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in results[: query.top_k]]

    def delete_document(self, document_id: str) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("DELETE FROM chunks WHERE document_id = ?", (document_id,))
            conn.commit()

    def rebuild_index(self) -> None:
        pass
