from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class Chunk(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    document_id: str = ""
    content: str = ""
    source: str = ""
    page: int | None = None
    section: str | None = None
    content_hash: str = ""
    parser_version: str = ""
    embedding: list[float] | None = None
    namespace: str = "personal"


class RAGQuery(BaseModel):
    query: str = ""
    namespace: str = "personal"
    top_k: int = 5
