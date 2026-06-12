from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from ya.application.cron_service import CronService
from ya.application.memory_service import MemoryService


class TestCronService:
    @pytest.fixture
    def db_path(self) -> Path:
        with tempfile.TemporaryDirectory(prefix="ya-cron-test-") as tmp:
            yield Path(tmp) / "scheduler.db"

    @pytest.mark.asyncio
    async def test_add_and_list(self, db_path: Path) -> None:
        svc = CronService(db_path)
        jid = await svc.add_job("Test Job", "daily:09:00", "prompt")
        assert len(jid) == 12

        jobs = await svc.list_jobs()
        assert len(jobs) == 1
        assert jobs[0]["name"] == "Test Job"

    @pytest.mark.asyncio
    async def test_pause_and_resume(self, db_path: Path) -> None:
        svc = CronService(db_path)
        jid = await svc.add_job("Pausable", "daily:08:00")

        assert await svc.pause_job(jid)
        jobs = await svc.list_jobs()
        assert jobs[0]["status"] == "paused"

        assert await svc.resume_job(jid)
        jobs = await svc.list_jobs()
        assert jobs[0]["status"] == "active"

    @pytest.mark.asyncio
    async def test_remove_existing(self, db_path: Path) -> None:
        svc = CronService(db_path)
        jid = await svc.add_job("To Remove")
        assert await svc.remove_job(jid)
        jobs = await svc.list_jobs()
        assert len(jobs) == 0

    @pytest.mark.asyncio
    async def test_remove_nonexistent(self, db_path: Path) -> None:
        svc = CronService(db_path)
        assert not await svc.remove_job("nonexistent")

    @pytest.mark.asyncio
    async def test_pause_nonexistent(self, db_path: Path) -> None:
        svc = CronService(db_path)
        assert not await svc.pause_job("nonexistent")

    @pytest.mark.asyncio
    async def test_run_job(self, db_path: Path) -> None:
        svc = CronService(db_path)
        jid = await svc.add_job("Daily", "daily:09:00", "daily_review")
        result = await svc.run_job(jid)
        assert result is not None
        assert result["status"] == "succeeded"


class TestMemoryService:
    @pytest.fixture
    def memory_path(self) -> Path:
        with tempfile.TemporaryDirectory(prefix="ya-mem-test-") as tmp:
            yield Path(tmp)

    @pytest.mark.asyncio
    async def test_add_and_search(self, memory_path: Path) -> None:
        svc = MemoryService(memory_path)
        mid = await svc.add("Python Tips", "Use list comprehensions", "semantic", "python,tips")
        assert mid.startswith("mem-")

        results = await svc.search(query="comprehensions")
        assert len(results) == 1
        assert results[0]["title"] == "Python Tips"

    @pytest.mark.asyncio
    async def test_show_memory(self, memory_path: Path) -> None:
        svc = MemoryService(memory_path)
        mid = await svc.add("Note", "Hello world")
        mem = await svc.show(mid)
        assert mem is not None
        assert mem["content"] == "Hello world"

    @pytest.mark.asyncio
    async def test_show_nonexistent(self, memory_path: Path) -> None:
        svc = MemoryService(memory_path)
        assert await svc.show("mem-nonexistent") is None

    @pytest.mark.asyncio
    async def test_chinese_memory(self, memory_path: Path) -> None:
        svc = MemoryService(memory_path)
        mid = await svc.add("中文记忆", "这是一条中文测试", "semantic", "测试")
        mem = await svc.show(mid)
        assert mem is not None
        assert "中文" in mem["content"]
