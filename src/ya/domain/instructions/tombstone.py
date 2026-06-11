from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel


class TombstoneStatus(StrEnum):
    ACTIVE = "active"
    MARKED = "marked"
    DELETED = "deleted"


class SessionTombstone(BaseModel):
    session_id: str = ""
    status: TombstoneStatus = TombstoneStatus.ACTIVE
    marked_at: str | None = None
    deleted_at: str | None = None
    retention_days: int = 30
    reason: str = ""


class TombstoneStore:
    def __init__(self) -> None:
        self._tombstones: dict[str, SessionTombstone] = {}

    def mark_for_deletion(self, session_id: str, retention_days: int = 30, reason: str = "") -> SessionTombstone:
        tombstone = SessionTombstone(
            session_id=session_id,
            status=TombstoneStatus.MARKED,
            marked_at=datetime.now(UTC).isoformat(),
            retention_days=retention_days,
            reason=reason,
        )
        self._tombstones[session_id] = tombstone
        return tombstone

    def hard_delete(self, session_id: str) -> bool:
        tombstone = self._tombstones.get(session_id)
        if tombstone is None:
            return False
        if tombstone.status != TombstoneStatus.MARKED:
            return False
        tombstone.status = TombstoneStatus.DELETED
        tombstone.deleted_at = datetime.now(UTC).isoformat()
        return True

    def cancel_deletion(self, session_id: str) -> bool:
        tombstone = self._tombstones.get(session_id)
        if tombstone is None:
            return False
        if tombstone.status != TombstoneStatus.MARKED:
            return False
        tombstone.status = TombstoneStatus.ACTIVE
        return True

    def get(self, session_id: str) -> SessionTombstone | None:
        return self._tombstones.get(session_id)

    def list_marked(self) -> list[SessionTombstone]:
        return [t for t in self._tombstones.values() if t.status == TombstoneStatus.MARKED]

    def cleanup_expired(self) -> int:
        now = datetime.now(UTC)
        count = 0
        for t in list(self._tombstones.values()):
            if t.status == TombstoneStatus.MARKED and t.marked_at:
                marked = datetime.fromisoformat(t.marked_at)
                if (now - marked).days >= t.retention_days:
                    t.status = TombstoneStatus.DELETED
                    t.deleted_at = now.isoformat()
                    count += 1
        return count
