from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class ApprovalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    EXPIRED = "expired"


class ApprovalItem(BaseModel):
    id: str = ""
    capability: str = ""
    target: str = ""
    requested_by: str = ""
    reason: str = ""
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    expires_at: str | None = None
    decided_at: str | None = None


class ApprovalInbox:
    def __init__(self) -> None:
        self._items: dict[str, ApprovalItem] = {}

    def submit(self, item: ApprovalItem) -> str:
        import uuid
        item.id = uuid.uuid4().hex[:8]
        self._items[item.id] = item
        return item.id

    def approve(self, item_id: str) -> bool:
        item = self._items.get(item_id)
        if item is None or item.status != ApprovalStatus.PENDING:
            return False
        item.status = ApprovalStatus.APPROVED
        item.decided_at = datetime.now(UTC).isoformat()
        return True

    def deny(self, item_id: str) -> bool:
        item = self._items.get(item_id)
        if item is None or item.status != ApprovalStatus.PENDING:
            return False
        item.status = ApprovalStatus.DENIED
        item.decided_at = datetime.now(UTC).isoformat()
        return True

    def list_pending(self) -> list[ApprovalItem]:
        return [i for i in self._items.values() if i.status == ApprovalStatus.PENDING]

    def list_all(self) -> list[ApprovalItem]:
        return sorted(self._items.values(), key=lambda i: i.created_at, reverse=True)

    def expire_old(self, max_age_hours: float = 24.0) -> int:
        now = datetime.now(UTC)
        count = 0
        for item in self._items.values():
            if item.status == ApprovalStatus.PENDING and item.created_at:
                created = datetime.fromisoformat(item.created_at)
                if (now - created).total_seconds() > max_age_hours * 3600:
                    item.status = ApprovalStatus.EXPIRED
                    count += 1
        return count
