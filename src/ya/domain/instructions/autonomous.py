from __future__ import annotations

from datetime import UTC, datetime

from ya.domain.instructions.reports import DailyReport


class AutonomousService:
    def __init__(self) -> None:
        self._last_digest_at: str = ""

    def generate_daily_digest(
        self,
        sessions: list[dict[str, object]],
        memories: list[dict[str, object]],
        tasks: list[dict[str, object]],
    ) -> DailyReport:
        now = datetime.now(UTC)
        report = DailyReport(
            date=now.strftime("%Y-%m-%d"),
            active_sessions=len([s for s in sessions if s.get("status") == "active"]),
            total_messages=sum(int(str(s.get("message_count", 0))) for s in sessions),
            new_memories=len([m for m in memories if str(m.get("created_at", "")).startswith(now.strftime("%Y-%m-%d"))]),
            completed_tasks=len([t for t in tasks if t.get("status") == "done"]),
            cron_jobs_executed=0,
            highlights=[],
        )

        pending = [t for t in tasks if t.get("status") not in ("done", "backlog")]
        blocked = [s for s in sessions if s.get("status") == "blocked"]

        if pending:
            report.highlights.append(f"{len(pending)} tasks in progress")
        if blocked:
            report.highlights.append(f"{len(blocked)} sessions blocked")
        if report.active_sessions == 0:
            report.highlights.append("No active sessions — system is idle")
        if report.new_memories > 0:
            report.highlights.append(f"{report.new_memories} new memories today")

        self._last_digest_at = now.isoformat()
        return report

    def get_attention_items(
        self,
        sessions: list[dict[str, object]],
        tasks: list[dict[str, object]],
    ) -> list[str]:
        items: list[str] = []
        now = datetime.now(UTC)

        overdue = [t for t in tasks if t.get("status") in ("in_progress", "review") and t.get("updated_at", "")
                   and (now - datetime.fromisoformat(str(t["updated_at"]))).days > 3]
        if overdue:
            items.append(f"{len(overdue)} tasks overdue (>3 days)")

        idle_sessions = [s for s in sessions if s.get("status") == "active" and s.get("last_activity", "")
                         and (now - datetime.fromisoformat(str(s["last_activity"]))).days > 1]
        if idle_sessions:
            items.append(f"{len(idle_sessions)} sessions idle (>1 day)")

        return items


class LoopGuard:
    def __init__(self, max_depth: int = 3, max_jobs_per_run: int = 5) -> None:
        self._max_depth = max_depth
        self._max_jobs = max_jobs_per_run
        self._run_chain: list[str] = []

    def enter_run(self, run_id: str) -> bool:
        if len(self._run_chain) >= self._max_depth:
            return False
        if run_id in self._run_chain:
            return False
        self._run_chain.append(run_id)
        return True

    def exit_run(self, run_id: str) -> None:
        if run_id in self._run_chain:
            self._run_chain.remove(run_id)

    def can_create_job(self, recent_count: int) -> bool:
        return recent_count < self._max_jobs

    @property
    def depth(self) -> int:
        return len(self._run_chain)
