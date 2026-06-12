from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from ya.adapters.memory.markdown import MarkdownMemoryStore
from ya.application.cron_service import CronService
from ya.application.memory_service import MemoryService
from ya.scheduler.store import SchedulerStore


class TestCronService:
    @pytest.fixture
    async def store(self) -> SchedulerStore:
        with tempfile.TemporaryDirectory(prefix="ya-cron-svc-") as tmp:
            s = SchedulerStore(str(Path(tmp) / "sched.db"))
            await s.initialize()
            yield s
            await s.close()

    @pytest.mark.asyncio
    async def test_add_and_list(self, store: SchedulerStore) -> None:
        svc = CronService(store)
        jid = await svc.add_job("Test", "daily:09:00", "prompt")
        assert len(jid) == 12
        jobs = await svc.list_jobs()
        assert len(jobs) == 1

    @pytest.mark.asyncio
    async def test_pause_resume(self, store: SchedulerStore) -> None:
        svc = CronService(store)
        jid = await svc.add_job("Pausable")
        assert await svc.pause_job(jid)
        jobs = await svc.list_jobs()
        assert jobs[0]["status"] == "paused"
        assert await svc.resume_job(jid)
        assert (await svc.list_jobs())[0]["status"] == "active"

    @pytest.mark.asyncio
    async def test_remove(self, store: SchedulerStore) -> None:
        svc = CronService(store)
        jid = await svc.add_job("To Remove")
        assert await svc.remove_job(jid)
        assert not await svc.remove_job("nonexistent")


class TestMemoryService:
    @pytest.fixture
    def store(self) -> MarkdownMemoryStore:
        with tempfile.TemporaryDirectory(prefix="ya-mem-svc-") as tmp:
            yield MarkdownMemoryStore(Path(tmp))

    @pytest.mark.asyncio
    async def test_add_and_show(self, store: MarkdownMemoryStore) -> None:
        svc = MemoryService(store)
        mid = await svc.add("Note", "Hello")
        assert mid.startswith("mem-")
        mem = await svc.show(mid)
        assert mem is not None
        assert mem["content"] == "Hello"

    @pytest.mark.asyncio
    async def test_search(self, store: MarkdownMemoryStore) -> None:
        svc = MemoryService(store)
        await svc.add("Python", "List comprehensions", tags="python")
        await svc.add("Rust", "Ownership rules", tags="rust")
        results = await svc.search(query="comprehensions")
        assert len(results) == 1
