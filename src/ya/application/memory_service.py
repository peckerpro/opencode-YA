from __future__ import annotations

import uuid
from pathlib import Path

from ya.adapters.memory.markdown import MarkdownMemoryStore
from ya.config.paths import resolve_paths
from ya.config.settings import load_settings
from ya.domain.memory.models import Memory, MemoryQuery, MemoryType


class MemoryService:
    def __init__(self, memory_path: Path | None = None) -> None:
        if memory_path is None:
            settings = load_settings()
            paths = resolve_paths(settings)
            memory_path = paths.memory
        self._store = MarkdownMemoryStore(memory_path)

    async def add(self, title: str, content: str, memory_type: str = "semantic", tags: str = "") -> str:
        mem = Memory(
            id=f"mem-{uuid.uuid4().hex[:8]}",
            title=title,
            content=content,
            memory_type=MemoryType(memory_type),
            tags=[t.strip() for t in tags.split(",") if t.strip()],
        )
        await self._store.save(mem)
        return mem.id

    async def search(self, query: str = "", memory_type: str = "", limit: int = 20) -> list[dict[str, str]]:
        q = MemoryQuery(text_search=query, limit=limit)
        if memory_type:
            q.memory_type = MemoryType(memory_type)
        results = await self._store.search(q) if query else await self._store.list_all()
        return [{"id": m.id, "title": m.title, "type": m.memory_type.value, "tags": ",".join(m.tags[:3])} for m in results[:limit]]

    async def show(self, memory_id: str) -> dict[str, str] | None:
        mem = await self._store.get(memory_id)
        if mem is None:
            return None
        return {"id": mem.id, "title": mem.title, "content": mem.content, "type": mem.memory_type.value, "tags": ",".join(mem.tags)}
