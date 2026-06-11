from __future__ import annotations

from contextlib import suppress
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, Field


class DailyReport(BaseModel):
    date: str = Field(default_factory=lambda: datetime.now(UTC).strftime("%Y-%m-%d"))
    active_sessions: int = 0
    total_messages: int = 0
    new_memories: int = 0
    completed_tasks: int = 0
    cron_jobs_executed: int = 0
    highlights: list[str] = Field(default_factory=list)
    generated_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class ReportService:
    def __init__(self, reports_dir: Path) -> None:
        self._dir = reports_dir
        self._dir.mkdir(parents=True, exist_ok=True)

    def generate(self, data: dict[str, int]) -> DailyReport:
        report = DailyReport(
            active_sessions=data.get("active_sessions", 0),
            total_messages=data.get("total_messages", 0),
            new_memories=data.get("new_memories", 0),
            completed_tasks=data.get("completed_tasks", 0),
            cron_jobs_executed=data.get("cron_jobs_executed", 0),
        )
        return report

    def save(self, report: DailyReport) -> Path:
        path = self._dir / f"{report.date}.json"
        path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
        return path

    def load(self, date_str: str) -> DailyReport | None:
        path = self._dir / f"{date_str}.json"
        if not path.exists():
            return None
        return DailyReport.model_validate_json(path.read_text(encoding="utf-8"))

    def list_reports(self, limit: int = 30) -> list[DailyReport]:
        reports: list[DailyReport] = []
        for f in sorted(self._dir.glob("*.json"), reverse=True):
            with suppress(Exception):
                reports.append(DailyReport.model_validate_json(f.read_text(encoding="utf-8")))
            if len(reports) >= limit:
                break
        return reports
