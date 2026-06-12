from __future__ import annotations

import asyncio
import uuid
from contextlib import suppress
from datetime import UTC, datetime
from pathlib import Path

from ya.adapters.memory.markdown import MarkdownMemoryStore
from ya.domain.memory.models import Memory, MemoryQuery, MemoryType


class MemoryService:
    def __init__(self, store: MarkdownMemoryStore, memory_repo_path: Path | None = None) -> None:
        self._store = store
        self._repo_path = memory_repo_path

    async def add(self, title: str, content: str, memory_type: str = "semantic", tags: str = "") -> str:
        mem = Memory(
            id=f"mem-{uuid.uuid4().hex[:8]}",
            title=title,
            content=content,
            memory_type=MemoryType(memory_type),
            tags=[t.strip() for t in tags.split(",") if t.strip()],
            created_at=datetime.now(UTC).isoformat(),
        )
        await self._store.save(mem)
        await self._auto_sync(f"add: {title}")
        return mem.id

    async def search(self, query: str = "", memory_type: str = "", limit: int = 20) -> list[dict[str, str]]:
        q = MemoryQuery(text_search=query, limit=limit)
        if memory_type:
            q.memory_type = MemoryType(memory_type)
        results = await self._store.search(q) if query else await self._store.list_all()
        return [{"id": m.id, "title": m.title, "content": m.content[:300], "type": m.memory_type.value, "tags": ",".join(m.tags[:3])} for m in results[:limit]]

    async def show(self, memory_id: str) -> dict[str, str] | None:
        mem = await self._store.get(memory_id)
        if mem is None:
            return None
        return {"id": mem.id, "title": mem.title, "content": mem.content, "type": mem.memory_type.value, "tags": ",".join(mem.tags)}

    async def sync(self) -> str:
        if self._repo_path is None:
            return "No memory repo configured"
        return await self._git_sync("manual sync")

    async def _auto_sync(self, message: str) -> None:
        if self._repo_path is None or not self._repo_path.exists():
            return
        with suppress(Exception):
            await self._git_sync(message)

    async def _git_sync(self, message: str) -> str:
        repo = str(self._repo_path)
        results: list[str] = []
        for cmd, label in [
            (["git", "add", "-A"], "add"),
            (["git", "commit", "-m", f"ya: {message}"], "commit"),
            (["git", "push", "origin", "master"], "push"),
        ]:
            proc = await asyncio.create_subprocess_exec(*cmd, cwd=repo, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            stdout, stderr = await proc.communicate()
            _stdout = stdout.decode().strip()
            err = stderr.decode().strip()
            if proc.returncode != 0:
                if "nothing to commit" in err:
                    results.append(f"{label}: up-to-date")
                else:
                    results.append(f"{label}: error - {err[:60]}")
            else:
                results.append(f"{label}: ok")
        return "; ".join(results)
