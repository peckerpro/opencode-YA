from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import yaml

from ya.domain.memory.models import Memory, MemoryQuery, MemoryType


class MarkdownMemoryStore:
    def __init__(self, root_path: Path) -> None:
        self._root = root_path

    def _memory_path(self, memory: Memory) -> Path:
        if memory.memory_type == MemoryType.DAILY:
            dt = datetime.fromisoformat(memory.created_at)
            return self._root / "daily" / str(dt.year) / f"{dt.month:02d}" / f"{dt.strftime('%Y-%m-%d')}.md"
        if memory.memory_type == MemoryType.PROJECT:
            proj = memory.projects[0] if memory.projects else "general"
            return self._root / "projects" / proj / "index.md"
        if memory.memory_type == MemoryType.TOPIC:
            return self._root / "topics" / f"{memory.id}.md"
        return self._root / "episodes" / f"{memory.id}.md"

    def _serialize(self, memory: Memory) -> str:
        frontmatter = {
            "id": memory.id,
            "title": memory.title,
            "created_at": memory.created_at,
            "updated_at": memory.updated_at,
            "type": memory.memory_type.value,
            "tags": memory.tags,
            "projects": memory.projects,
            "source": memory.source,
        }
        fm_str = yaml.dump(frontmatter, allow_unicode=True, default_flow_style=False).strip()
        return f"---\n{fm_str}\n---\n\n{memory.content}\n"

    def _deserialize(self, text: str) -> Memory:
        if not text.startswith("---"):
            return Memory(content=text.strip())
        parts = text.split("---", 2)
        if len(parts) < 3:
            return Memory(content=text.strip())
        fm_data = yaml.safe_load(parts[1]) or {}
        content = parts[2].strip()
        return Memory(
            id=fm_data.get("id", ""),
            title=fm_data.get("title", ""),
            created_at=fm_data.get("created_at", ""),
            updated_at=fm_data.get("updated_at", ""),
            memory_type=MemoryType(fm_data.get("type", "semantic")),
            tags=fm_data.get("tags", []),
            projects=fm_data.get("projects", []),
            source=fm_data.get("source", "conversation"),
            content=content,
        )

    async def save(self, memory: Memory) -> None:
        memory.updated_at = datetime.now(UTC).isoformat()
        path = self._memory_path(memory)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self._serialize(memory), encoding="utf-8")

    async def get(self, memory_id: str) -> Memory | None:
        for md_file in self._root.rglob("*.md"):
            text = md_file.read_text(encoding="utf-8")
            mem = self._deserialize(text)
            if mem.id == memory_id:
                return mem
        return None

    async def delete(self, memory_id: str) -> None:
        for md_file in self._root.rglob("*.md"):
            text = md_file.read_text(encoding="utf-8")
            mem = self._deserialize(text)
            if mem.id == memory_id:
                md_file.unlink()
                return

    async def search(self, query: MemoryQuery) -> list[Memory]:
        results: list[Memory] = []
        for md_file in self._root.rglob("*.md"):
            text = md_file.read_text(encoding="utf-8")
            mem = self._deserialize(text)
            if query.memory_type and mem.memory_type != query.memory_type:
                continue
            if query.tags and not set(query.tags) & set(mem.tags):
                continue
            if query.project and query.project not in mem.projects:
                continue
            if query.text_search and query.text_search.lower() not in mem.content.lower():
                continue
            results.append(mem)
        results.sort(key=lambda m: m.updated_at, reverse=True)
        return results[: query.limit]

    async def list_all(self) -> list[Memory]:
        results: list[Memory] = []
        for md_file in self._root.rglob("*.md"):
            text = md_file.read_text(encoding="utf-8")
            results.append(self._deserialize(text))
        results.sort(key=lambda m: m.updated_at, reverse=True)
        return results
