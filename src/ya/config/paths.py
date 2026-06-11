from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ya.config.settings import Settings


@dataclass(frozen=True)
class ResolvedPaths:
    ya_home: Path
    state_db: Path
    logs: Path
    audit_logs: Path
    memory: Path
    rag: Path
    cron: Path
    tmp: Path
    workspace: Path


def resolve_paths(settings: Settings) -> ResolvedPaths:
    home = settings.ya_home_expanded
    return ResolvedPaths(
        ya_home=home,
        state_db=home / "state" / "ya.db",
        logs=home / "logs",
        audit_logs=home / "logs" / "audit",
        memory=home / "memory",
        rag=home / "rag",
        cron=home / "cron",
        tmp=home / "tmp",
        workspace=home / "workspace",
    )
