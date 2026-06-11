from __future__ import annotations

from abc import abstractmethod
from typing import Protocol, runtime_checkable


@runtime_checkable
class SyncBackend(Protocol):
    @abstractmethod
    async def status(self) -> dict[str, str]: ...

    @abstractmethod
    async def pull(self) -> str: ...

    @abstractmethod
    async def commit_and_push(self, message: str) -> str: ...
