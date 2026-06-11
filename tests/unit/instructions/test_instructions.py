from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from ya.domain.instructions.queue import InstructionItem, InstructionQueue, Priority
from ya.domain.instructions.reports import DailyReport, ReportService
from ya.domain.instructions.tombstone import TombstoneStatus, TombstoneStore


class TestInstructionQueue:
    @pytest.fixture
    def queue(self) -> InstructionQueue:
        return InstructionQueue(rate_limit_per_minute=100)

    def test_enqueue_and_dequeue(self, queue: InstructionQueue) -> None:
        item = InstructionItem(
            id="i1", target_session_id="s1",
            content="Hello", priority=Priority.NORMAL,
        )
        queue.enqueue(item)
        assert queue.pending_count() == 1

        dequeued = queue.dequeue("s1")
        assert dequeued is not None
        assert dequeued.id == "i1"
        assert dequeued.status == "delivered"

    def test_priority_ordering(self, queue: InstructionQueue) -> None:
        queue.enqueue(InstructionItem(id="low", target_session_id="s1", priority=Priority.LOW))
        queue.enqueue(InstructionItem(id="critical", target_session_id="s1", priority=Priority.CRITICAL))
        queue.enqueue(InstructionItem(id="normal", target_session_id="s1", priority=Priority.NORMAL))

        first = queue.dequeue("s1")
        assert first is not None
        assert first.id == "critical"

    def test_cancel(self, queue: InstructionQueue) -> None:
        item = InstructionItem(id="i1", target_session_id="s1", content="Test")
        queue.enqueue(item)
        assert queue.cancel("i1")
        assert queue.pending_count() == 0

    def test_complete(self, queue: InstructionQueue) -> None:
        item = InstructionItem(id="i1", target_session_id="s1", content="Test")
        queue.enqueue(item)
        queue.dequeue("s1")
        assert queue.complete("i1", "Done")
        assert len(queue.get_history()) == 1

    def test_rate_limit(self) -> None:
        queue = InstructionQueue(rate_limit_per_minute=1)
        queue.enqueue(InstructionItem(id="a", target_session_id="s1"))
        queue.enqueue(InstructionItem(id="b", target_session_id="s1"))

        first = queue.dequeue("s1")
        assert first is not None
        second = queue.dequeue("s1")
        assert second is None


class TestReportService:
    @pytest.fixture
    def service(self) -> ReportService:
        with tempfile.TemporaryDirectory() as tmp:
            yield ReportService(Path(tmp))

    def test_generate_and_save(self, service: ReportService) -> None:
        report = service.generate({"active_sessions": 3, "completed_tasks": 5})
        assert report.active_sessions == 3

        path = service.save(report)
        assert path.exists()

    def test_load_and_list(self, service: ReportService) -> None:
        r1 = DailyReport(date="2026-01-01", active_sessions=1)
        service.save(r1)
        r2 = DailyReport(date="2026-01-02", active_sessions=2)
        service.save(r2)

        loaded = service.load("2026-01-01")
        assert loaded is not None
        assert loaded.active_sessions == 1

        reports = service.list_reports()
        assert len(reports) == 2


class TestTombstoneStore:
    @pytest.fixture
    def store(self) -> TombstoneStore:
        return TombstoneStore()

    def test_mark_and_hard_delete(self, store: TombstoneStore) -> None:
        store.mark_for_deletion("s1", retention_days=7, reason="cleanup")
        assert store.get("s1") is not None

        assert store.hard_delete("s1")
        t = store.get("s1")
        assert t is not None
        assert t.status == TombstoneStatus.DELETED

    def test_cancel_deletion(self, store: TombstoneStore) -> None:
        store.mark_for_deletion("s1")
        assert store.cancel_deletion("s1")
        t = store.get("s1")
        assert t is not None
        assert t.status == TombstoneStatus.ACTIVE

    def test_cannot_delete_active(self, store: TombstoneStore) -> None:
        assert not store.hard_delete("nonexistent")

    def test_list_marked(self, store: TombstoneStore) -> None:
        store.mark_for_deletion("s1")
        store.mark_for_deletion("s2")
        store.hard_delete("s1")
        marked = store.list_marked()
        assert len(marked) == 1
        assert marked[0].session_id == "s2"

    def test_cleanup_expired(self, store: TombstoneStore) -> None:
        store.mark_for_deletion("s1", retention_days=0)
        count = store.cleanup_expired()
        assert count == 1
        t = store.get("s1")
        assert t is not None
        assert t.status == TombstoneStatus.DELETED
