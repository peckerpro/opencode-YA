from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class MessageRole(StrEnum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ToolCallRequest(BaseModel):
    id: str
    name: str
    arguments: str


class Message(BaseModel):
    role: MessageRole
    content: str | None = None
    tool_calls: list[ToolCallRequest] | None = None
    tool_call_id: str | None = None
    name: str | None = None
    created_at: str = Field(default_factory=lambda: "")


class LLMStreamEvent(BaseModel):
    event_type: str
    content_delta: str | None = None
    tool_call_delta: ToolCallRequest | None = None
    finish_reason: str | None = None
    usage: dict[str, int] | None = None


class LLMResponse(BaseModel):
    content: str | None = None
    tool_calls: list[ToolCallRequest] | None = None
    finish_reason: str | None = None
    usage: dict[str, int] | None = None


class LLMError(Exception):
    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        provider: str = "",
        retryable: bool = False,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.provider = provider
        self.retryable = retryable
