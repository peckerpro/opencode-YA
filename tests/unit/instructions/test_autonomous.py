from __future__ import annotations

from ya.domain.instructions.autonomous import AutonomousService, LoopGuard


class TestAutonomousService:
    def test_generate_digest_with_activity(self) -> None:
        svc = AutonomousService()
        sessions = [{"id": "s1", "status": "active", "message_count": 10}]
        memories = [{"created_at": "2026-06-12T00:00:00Z"}]
        tasks = [{"status": "done"}, {"status": "in_progress"}]

        report = svc.generate_daily_digest(sessions, memories, tasks)
        assert report.active_sessions == 1
        assert report.total_messages == 10
        assert len(report.highlights) >= 1

    def test_idle_detection(self) -> None:
        svc = AutonomousService()
        report = svc.generate_daily_digest([], [], [])
        assert report.active_sessions == 0
        assert any("idle" in h.lower() for h in report.highlights)

    def test_attention_overdue_tasks(self) -> None:
        svc = AutonomousService()
        tasks = [{"status": "in_progress", "updated_at": "2026-01-01T00:00:00Z"}]
        items = svc.get_attention_items([], tasks)
        assert len(items) >= 1
        assert "overdue" in items[0].lower()


class TestLoopGuard:
    def test_allows_within_depth(self) -> None:
        guard = LoopGuard(max_depth=3)
        assert guard.enter_run("r1")
        assert guard.enter_run("r2")
        assert guard.depth == 2

    def test_rejects_exceed_depth(self) -> None:
        guard = LoopGuard(max_depth=2)
        assert guard.enter_run("r1")
        assert guard.enter_run("r2")
        assert not guard.enter_run("r3")

    def test_rejects_duplicate(self) -> None:
        guard = LoopGuard()
        assert guard.enter_run("r1")
        assert not guard.enter_run("r1")

    def test_can_create_job(self) -> None:
        guard = LoopGuard(max_jobs_per_run=3)
        assert guard.can_create_job(0)
        assert guard.can_create_job(2)
        assert not guard.can_create_job(5)
