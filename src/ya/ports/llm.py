from __future__ import annotations

from abc import abstractmethod
from collections.abc import AsyncIterator
from typing import Protocol, runtime_checkable

from ya.domain.messages.models import (
    LLMResponse,
    LLMStreamEvent,
    Message,
)
from ya.ports.tools import ToolDefinition


@runtime_checkable
class LLMProvider(Protocol):
    @abstractmethod
    async def generate(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
    ) -> LLMResponse: ...

    @abstractmethod
    async def generate_stream(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
    ) -> AsyncIterator[LLMStreamEvent]: ...
