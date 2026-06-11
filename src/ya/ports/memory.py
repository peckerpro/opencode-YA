from __future__ import annotations

from abc import abstractmethod
from typing import Protocol, runtime_checkable

from ya.domain.memory.models import Memory, MemoryQuery


@runtime_checkable
class MemoryStore(Protocol):
    @abstractmethod
    async def save(self, memory: Memory) -> None: ...

    @abstractmethod
    async def get(self, memory_id: str) -> Memory | None: ...

    @abstractmethod
    async def delete(self, memory_id: str) -> None: ...

    @abstractmethod
    async def search(self, query: MemoryQuery) -> list[Memory]: ...

    @abstractmethod
    async def list_all(self) -> list[Memory]: ...
