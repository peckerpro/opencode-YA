from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from ya.adapters.memory.markdown import MarkdownMemoryStore
from ya.domain.memory.models import Memory, MemoryQuery, MemoryType


@pytest.fixture
def store() -> MarkdownMemoryStore:
    with tempfile.TemporaryDirectory(prefix="ya-memory-") as tmp:
        yield MarkdownMemoryStore(Path(tmp))


class TestMarkdownMemoryStore:
    @pytest.mark.asyncio
    async def test_save_and_get(self, store: MarkdownMemoryStore) -> None:
        mem = Memory(
            id="mem-001",
            title="Test Memory",
            memory_type=MemoryType.SEMANTIC,
            tags=["test"],
            content="Hello, memory!",
        )
        await store.save(mem)

        retrieved = await store.get("mem-001")
        assert retrieved is not None
        assert retrieved.title == "Test Memory"
        assert retrieved.content == "Hello, memory!"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, store: MarkdownMemoryStore) -> None:
        assert await store.get("nonexistent") is None

    @pytest.mark.asyncio
    async def test_delete(self, store: MarkdownMemoryStore) -> None:
        mem = Memory(id="mem-002", content="Delete me")
        await store.save(mem)
        await store.delete("mem-002")
        assert await store.get("mem-002") is None

    @pytest.mark.asyncio
    async def test_search_by_type(self, store: MarkdownMemoryStore) -> None:
        await store.save(Memory(id="m1", memory_type=MemoryType.SEMANTIC, content="First"))
        await store.save(Memory(id="m2", memory_type=MemoryType.PROJECT, content="Second"))

        results = await store.search(MemoryQuery(memory_type=MemoryType.SEMANTIC))
        assert len(results) == 1
        assert results[0].id == "m1"

    @pytest.mark.asyncio
    async def test_search_by_text(self, store: MarkdownMemoryStore) -> None:
        await store.save(Memory(id="m1", content="Python programming tips"))
        await store.save(Memory(id="m2", content="Rust ownership rules"))

        results = await store.search(MemoryQuery(text_search="python"))
        assert len(results) == 1
        assert results[0].id == "m1"

    @pytest.mark.asyncio
    async def test_search_by_tag(self, store: MarkdownMemoryStore) -> None:
        await store.save(Memory(id="m1", tags=["ya", "python"], content="A"))
        await store.save(Memory(id="m2", tags=["rust"], content="B"))

        results = await store.search(MemoryQuery(tags=["ya"]))
        assert len(results) == 1
        assert results[0].id == "m1"

    @pytest.mark.asyncio
    async def test_list_all(self, store: MarkdownMemoryStore) -> None:
        await store.save(Memory(id="m1", content="A"))
        await store.save(Memory(id="m2", content="B"))

        all_mems = await store.list_all()
        assert len(all_mems) == 2

    @pytest.mark.asyncio
    async def test_chinese_content(self, store: MarkdownMemoryStore) -> None:
        mem = Memory(id="mem-cn", title="中文记忆", content="这是一条中文记忆内容。")
        await store.save(mem)

        retrieved = await store.get("mem-cn")
        assert retrieved is not None
        assert retrieved.title == "中文记忆"
        assert "中文记忆内容" in retrieved.content

    @pytest.mark.asyncio
    async def test_frontmatter_roundtrip(self, store: MarkdownMemoryStore) -> None:
        mem = Memory(
            id="mem-fm",
            title="Frontmatter Test",
            memory_type=MemoryType.DAILY,
            tags=["test", "frontmatter"],
            projects=["YA"],
            source="conversation",
            content="Testing frontmatter serialization.",
        )
        await store.save(mem)

        retrieved = await store.get("mem-fm")
        assert retrieved is not None
        assert retrieved.tags == ["test", "frontmatter"]
        assert retrieved.projects == ["YA"]
        assert retrieved.memory_type == MemoryType.DAILY

    @pytest.mark.asyncio
    async def test_daily_path_structure(self, store: MarkdownMemoryStore) -> None:
        mem = Memory(
            id="mem-daily",
            memory_type=MemoryType.DAILY,
            created_at="2026-06-11T10:00:00+00:00",
            content="Daily note",
        )
        await store.save(mem)

        retrieved = await store.get("mem-daily")
        assert retrieved is not None
