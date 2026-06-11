from __future__ import annotations

from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, patch

import pytest
from openai.types.chat import ChatCompletion, ChatCompletionChunk

from ya.adapters.llm.minimax import MiniMaxProvider
from ya.domain.messages.models import (
    LLMError,
    LLMResponse,
    Message,
    MessageRole,
)
from ya.ports.tools import ToolDefinition


@pytest.fixture
def provider() -> MiniMaxProvider:
    return MiniMaxProvider(api_key="test-key", model="MiniMax-M3")


class TestMiniMaxProvider:
    def test_init_stores_config(self) -> None:
        p = MiniMaxProvider(
            api_key="sk-abc",
            base_url="https://custom.api/v1",
            model="custom-model",
            timeout=30.0,
        )
        assert p._model == "custom-model"

    @pytest.mark.asyncio
    async def test_generate_returns_response(self, provider: MiniMaxProvider) -> None:
        mock_response = ChatCompletion.model_validate({
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "MiniMax-M3",
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": "Hello!"},
                "finish_reason": "stop",
            }],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        })

        with patch.object(provider._client.chat.completions, "create",
                          AsyncMock(return_value=mock_response)):
            result = await provider.generate(
                messages=[Message(role=MessageRole.USER, content="Hi")]
            )
            assert isinstance(result, LLMResponse)
            assert result.content == "Hello!"
            assert result.finish_reason == "stop"

    @pytest.mark.asyncio
    async def test_generate_auth_error(self, provider: MiniMaxProvider) -> None:
        from httpx import Request, Response
        from openai import AuthenticationError

        request = Request("POST", "https://api.minimaxi.com/v1/chat/completions")
        response = Response(401, request=request)
        mock_error = AuthenticationError(
            "bad key", response=response, body={"error": "invalid key"}
        )
        with patch.object(provider._client.chat.completions, "create",
                          AsyncMock(side_effect=mock_error)):
            with pytest.raises(LLMError) as exc:
                await provider.generate(messages=[Message(role=MessageRole.USER, content="Hi")])
            assert exc.value.status_code == 401
            assert not exc.value.retryable

    @pytest.mark.asyncio
    async def test_generate_rate_limit_error(self, provider: MiniMaxProvider) -> None:
        from httpx import Request, Response
        from openai import RateLimitError

        request = Request("POST", "https://api.minimaxi.com/v1/chat/completions")
        response = Response(429, request=request)
        mock_error = RateLimitError(
            "too many", response=response, body={"error": "rate limit"}
        )
        with patch.object(provider._client.chat.completions, "create",
                          AsyncMock(side_effect=mock_error)):
            with pytest.raises(LLMError) as exc:
                await provider.generate(messages=[Message(role=MessageRole.USER, content="Hi")])
            assert exc.value.status_code == 429
            assert exc.value.retryable

    @pytest.mark.asyncio
    async def test_generate_timeout_error(self, provider: MiniMaxProvider) -> None:
        from openai import APITimeoutError

        with patch.object(provider._client.chat.completions, "create",
                          AsyncMock(side_effect=APITimeoutError("timeout"))):
            with pytest.raises(LLMError) as exc:
                await provider.generate(messages=[Message(role=MessageRole.USER, content="Hi")])
            assert exc.value.retryable

    @pytest.mark.asyncio
    async def test_generate_with_tool_calls(self, provider: MiniMaxProvider) -> None:
        mock_response = ChatCompletion.model_validate({
            "id": "chatcmpl-456",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "MiniMax-M3",
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": "call_1",
                        "type": "function",
                        "function": {"name": "utc_time", "arguments": "{}"},
                    }],
                },
                "finish_reason": "tool_calls",
            }],
        })

        with patch.object(provider._client.chat.completions, "create",
                          AsyncMock(return_value=mock_response)):
            result = await provider.generate(
                messages=[Message(role=MessageRole.USER, content="What time is it?")],
                tools=[ToolDefinition(
                    name="utc_time", description="Get UTC time",
                    parameters={"type": "object", "properties": {}},
                )],
            )
            assert result.tool_calls is not None
            assert result.tool_calls[0].name == "utc_time"
            assert result.tool_calls[0].arguments == "{}"

    @pytest.mark.asyncio
    async def test_stream_yields_text_events(self, provider: MiniMaxProvider) -> None:
        chunks = [
            ChatCompletionChunk.model_validate({
                "id": "chatcmpl-789",
                "object": "chat.completion.chunk",
                "created": 1234567890,
                "model": "MiniMax-M3",
                "choices": [{"index": 0, "delta": {"content": "Hello"}, "finish_reason": None}],
            }),
            ChatCompletionChunk.model_validate({
                "id": "chatcmpl-789",
                "object": "chat.completion.chunk",
                "created": 1234567890,
                "model": "MiniMax-M3",
                "choices": [{"index": 0, "delta": {"content": " world"}, "finish_reason": None}],
            }),
            ChatCompletionChunk.model_validate({
                "id": "chatcmpl-789",
                "object": "chat.completion.chunk",
                "created": 1234567890,
                "model": "MiniMax-M3",
                "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
            }),
        ]

        async def mock_stream() -> AsyncIterator[ChatCompletionChunk]:
            for c in chunks:
                yield c

        with patch.object(provider._client.chat.completions, "create",
                          AsyncMock(return_value=mock_stream())):
            events = []
            async for event in provider.generate_stream(
                messages=[Message(role=MessageRole.USER, content="Hi")]
            ):
                events.append(event)

            text_events = [e for e in events if e.event_type == "text_delta"]
            assert len(text_events) == 2
            assert text_events[0].content_delta == "Hello"
            assert text_events[1].content_delta == " world"

            finish_events = [e for e in events if e.event_type == "finish"]
            assert len(finish_events) == 1
            assert finish_events[0].finish_reason == "stop"
