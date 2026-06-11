from __future__ import annotations

import uuid
from collections import deque
from datetime import UTC, datetime
from enum import IntEnum

from pydantic import BaseModel, Field


class Priority(IntEnum):
    LOW = 0
    NORMAL = 5
    HIGH = 8
    CRITICAL = 10


class QueueStatus(BaseModel):
    status: str = "queued"


class InstructionItem(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:8])
    source_session_id: str = ""
    target_session_id: str = ""
    content: str = ""
    priority: Priority = Priority.NORMAL
    status: str = "queued"
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    delivered_at: str | None = None
    completed_at: str | None = None
    result: str = ""
    max_retries: int = 3
    retry_count: int = 0


class InstructionQueue:
    def __init__(self, rate_limit_per_minute: int = 10) -> None:
        self._queue: deque[InstructionItem] = deque()
        self._active: dict[str, InstructionItem] = {}
        self._history: list[InstructionItem] = []
        self._rate_limit = rate_limit_per_minute
        self._delivery_count: dict[str, int] = {}

    def enqueue(self, item: InstructionItem) -> str:
        self._queue.append(item)
        self._queue = deque(sorted(self._queue, key=lambda x: x.priority.value, reverse=True))
        return item.id

    def dequeue(self, target_session_id: str) -> InstructionItem | None:
        now = datetime.now(UTC)
        minute_key = f"{target_session_id}:{now.strftime('%Y%m%d%H%M')}"
        count = self._delivery_count.get(minute_key, 0)
        if count >= self._rate_limit:
            return None

        for _i, item in enumerate(self._queue):
            if item.target_session_id == target_session_id and item.status == "queued":
                self._queue.remove(item)
                item.status = "delivered"
                item.delivered_at = now.isoformat()
                self._active[item.id] = item
                self._delivery_count[minute_key] = count + 1
                return item
        return None

    def complete(self, instruction_id: str, result: str = "") -> bool:
        item = self._active.pop(instruction_id, None)
        if item is None:
            for it in self._queue:
                if it.id == instruction_id:
                    item = it
                    self._queue.remove(it)
                    break
        if item is None:
            return False
        item.status = "completed"
        item.completed_at = datetime.now(UTC).isoformat()
        item.result = result
        self._history.append(item)
        return True

    def cancel(self, instruction_id: str) -> bool:
        for item in self._queue:
            if item.id == instruction_id:
                item.status = "cancelled"
                self._history.append(item)
                self._queue.remove(item)
                return True
        return False

    def pending_count(self, target_session_id: str | None = None) -> int:
        if target_session_id:
            return sum(1 for i in self._queue if i.target_session_id == target_session_id)
        return len(self._queue)

    def get_pending(self, target_session_id: str | None = None) -> list[InstructionItem]:
        items = list(self._queue)
        if target_session_id:
            items = [i for i in items if i.target_session_id == target_session_id]
        return sorted(items, key=lambda x: x.priority.value, reverse=True)

    def get_history(self, limit: int = 50) -> list[InstructionItem]:
        return sorted(self._history, key=lambda x: x.created_at, reverse=True)[:limit]
