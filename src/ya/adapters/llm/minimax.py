from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

from openai import AsyncOpenAI

from ya.domain.messages.models import (
    LLMError,
    LLMResponse,
    LLMStreamEvent,
    Message,
    ToolCallRequest,
)
from ya.ports.tools import ToolDefinition


class MiniMaxProvider:
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.minimaxi.com/v1",
        model: str = "MiniMax-M3",
        timeout: float = 60.0,
    ) -> None:
        self._model = model
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
        )

    async def generate(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
    ) -> LLMResponse:
        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=self._to_openai_messages(messages),  # type: ignore[arg-type]
                tools=self._to_openai_tools(tools),  # type: ignore[arg-type]
            )
            return self._parse_response(response)
        except Exception as e:
            raise self._normalize_error(e) from e

    async def generate_stream(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
    ) -> AsyncIterator[LLMStreamEvent]:
        try:
            stream = await self._client.chat.completions.create(
                model=self._model,
                messages=self._to_openai_messages(messages),  # type: ignore[arg-type]
                tools=self._to_openai_tools(tools),  # type: ignore[arg-type]
                stream=True,
            )
            tool_call_buffers: dict[int, dict[str, str]] = {}
            async for chunk in stream:  # type: ignore[union-attr]
                delta = chunk.choices[0].delta if chunk.choices else None
                if delta is None:
                    continue

                if delta.content:
                    yield LLMStreamEvent(
                        event_type="text_delta",
                        content_delta=delta.content,
                    )

                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        idx = tc.index
                        if idx not in tool_call_buffers:
                            tool_call_buffers[idx] = {
                                "id": tc.id or "",
                                "name": (tc.function.name if tc.function and tc.function.name else ""),
                                "arguments": "",
                            }
                        buf = tool_call_buffers[idx]
                        if tc.id:
                            buf["id"] = tc.id
                        if tc.function:
                            if tc.function.name:
                                buf["name"] = tc.function.name
                            if tc.function.arguments:
                                buf["arguments"] += tc.function.arguments

                finish = chunk.choices[0].finish_reason if chunk.choices else None
                if finish:
                    for buf in tool_call_buffers.values():
                        buf["arguments"] = self._validate_json_args(
                            buf["arguments"]
                        )
                        yield LLMStreamEvent(
                            event_type="tool_call",
                            tool_call_delta=ToolCallRequest(
                                id=buf["id"],
                                name=buf["name"],
                                arguments=buf["arguments"],
                            ),
                        )
                    yield LLMStreamEvent(
                        event_type="finish",
                        finish_reason=finish,
                        usage={"total_tokens": 0},
                    )
        except Exception as e:
            raise self._normalize_error(e) from e

    def _to_openai_messages(self, messages: list[Message]) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for msg in messages:
            entry: dict[str, Any] = {"role": msg.role.value}
            if msg.content is not None:
                entry["content"] = msg.content
            if msg.tool_calls:
                entry["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.name,
                            "arguments": tc.arguments,
                        },
                    }
                    for tc in msg.tool_calls
                ]
            if msg.tool_call_id:
                entry["tool_call_id"] = msg.tool_call_id
            if msg.name:
                entry["name"] = msg.name
            result.append(entry)
        return result

    @staticmethod
    def _to_openai_tools(
        tools: list[ToolDefinition] | None,
    ) -> list[dict[str, Any]] | None:
        if not tools:
            return None
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            }
            for t in tools
        ]

    @staticmethod
    def _parse_response(response: Any) -> LLMResponse:
        choice = response.choices[0]
        msg = choice.message
        tool_calls = None
        if msg.tool_calls:
            tool_calls = [
                ToolCallRequest(
                    id=tc.id,
                    name=tc.function.name,
                    arguments=tc.function.arguments,
                )
                for tc in msg.tool_calls
            ]
        usage = None
        if response.usage:
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }
        return LLMResponse(
            content=msg.content,
            tool_calls=tool_calls,
            finish_reason=choice.finish_reason,
            usage=usage,
        )

    @staticmethod
    def _validate_json_args(args: str) -> str:
        try:
            json.loads(args)
            return args
        except json.JSONDecodeError:
            return args

    def _normalize_error(self, error: object) -> LLMError:
        from openai import (
            APIConnectionError,
            APIStatusError,
            APITimeoutError,
            AuthenticationError,
            RateLimitError,
        )

        if isinstance(error, AuthenticationError):
            return LLMError(
                message="Authentication failed — check your API key",
                status_code=401,
                provider="minimax",
                retryable=False,
            )
        if isinstance(error, RateLimitError):
            return LLMError(
                message="Rate limit exceeded",
                status_code=429,
                provider="minimax",
                retryable=True,
            )
        if isinstance(error, APITimeoutError):
            return LLMError(
                message="Request timed out",
                provider="minimax",
                retryable=True,
            )
        if isinstance(error, APIConnectionError):
            return LLMError(
                message="Connection failed",
                provider="minimax",
                retryable=True,
            )
        if isinstance(error, APIStatusError):
            return LLMError(
                message=f"API error: {error.message}",
                status_code=error.status_code,
                provider="minimax",
                retryable=error.status_code >= 500,
            )
        return LLMError(
            message=str(error),
            provider="minimax",
            retryable=False,
        )
