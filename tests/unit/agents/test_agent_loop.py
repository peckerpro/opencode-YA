from __future__ import annotations

from collections.abc import AsyncIterator

import pytest

from ya.adapters.stores.sqlite import SqliteSessionStore
from ya.application.chat import AgentLoop, AgentLoopConfig
from ya.domain.messages.models import (
    LLMResponse,
    LLMStreamEvent,
    Message,
    MessageRole,
    ToolCallRequest,
)
from ya.domain.sessions.models import Session
from ya.ports.tools import ToolDefinition
from ya.tools.builtin.utc_time import UtcTimeTool
from ya.tools.policy import PermissionPolicy
from ya.tools.registry import ToolRegistry


class FakeProvider:
    def __init__(self) -> None:
        self._responses: list[LLMResponse] = []
        self.call_count = 0

    def set_responses(self, responses: list[LLMResponse]) -> None:
        self._responses = list(responses)

    async def generate(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
    ) -> LLMResponse:
        idx = min(self.call_count, len(self._responses) - 1)
        self.call_count += 1
        return self._responses[idx] if self._responses else LLMResponse(content="")

    async def generate_stream(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
    ) -> AsyncIterator[LLMStreamEvent]:
        idx = min(self.call_count, len(self._responses) - 1)
        self.call_count += 1
        resp = self._responses[idx] if self._responses else LLMResponse(content="")
        if resp.content:
            yield LLMStreamEvent(event_type="text_delta", content_delta=resp.content)
            yield LLMStreamEvent(event_type="finish", finish_reason="stop")
        if resp.tool_calls:
            for tc in resp.tool_calls:
                yield LLMStreamEvent(event_type="tool_call", tool_call_delta=tc)
            yield LLMStreamEvent(event_type="finish", finish_reason="tool_calls")


@pytest.fixture
async def store() -> SqliteSessionStore:
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory(prefix="ya-test-loop-") as tmp:
        s = SqliteSessionStore(Path(tmp) / "ya.db")
        await s.initialize()
        yield s
        await s.close()


@pytest.fixture
def fake_provider() -> FakeProvider:
    return FakeProvider()


@pytest.fixture
def registry() -> ToolRegistry:
    r = ToolRegistry()
    r.register(UtcTimeTool())
    return r


@pytest.fixture
def policy() -> PermissionPolicy:
    return PermissionPolicy()


@pytest.fixture
def loop(
    fake_provider: FakeProvider,
    store: SqliteSessionStore,
    registry: ToolRegistry,
    policy: PermissionPolicy,
) -> AgentLoop:
    return AgentLoop(
        provider=fake_provider,
        store=store,
        policy=policy,
        config=AgentLoopConfig(max_steps=5),
    )


class TestAgentLoop:
    @pytest.mark.asyncio
    async def test_simple_text_response(
        self, loop: AgentLoop, store: SqliteSessionStore, fake_provider: FakeProvider
    ) -> None:
        fake_provider.set_responses([LLMResponse(content="Hello, world!", finish_reason="stop")])
        session = Session(id="s1", title="Test")
        await store.create_session(session)

        run = await loop.run(session, "Hi")

        assert run.status.value == "completed"
        messages = await store.get_messages("s1")
        assert len(messages) == 3
        assert messages[2].content == "Hello, world!"

    @pytest.mark.asyncio
    async def test_multi_turn_context(
        self, loop: AgentLoop, store: SqliteSessionStore, fake_provider: FakeProvider
    ) -> None:
        fake_provider.set_responses([
            LLMResponse(content="First response", finish_reason="stop"),
            LLMResponse(content="Second response", finish_reason="stop"),
        ])
        session = Session(id="s1")
        await store.create_session(session)

        await loop.run(session, "Turn 1")
        await loop.run(session, "Turn 2")

        messages = await store.get_messages("s1")
        assert len(messages) == 5

    @pytest.mark.asyncio
    async def test_tool_call_loop(
        self, loop: AgentLoop, store: SqliteSessionStore, fake_provider: FakeProvider
    ) -> None:
        fake_provider.set_responses([
            LLMResponse(
                tool_calls=[ToolCallRequest(id="call1", name="utc_time", arguments="{}")],
                finish_reason="tool_calls",
            ),
            LLMResponse(content="The time is now displayed.", finish_reason="stop"),
        ])
        session = Session(id="s1")
        await store.create_session(session)

        run = await loop.run(session, "What time is it?")

        assert run.status.value == "completed"
        messages = await store.get_messages("s1")
        tool_msgs = [m for m in messages if m.role == MessageRole.TOOL]
        assert len(tool_msgs) == 1
        assert "T" in tool_msgs[0].content or tool_msgs[0].content is not None

    @pytest.mark.asyncio
    async def test_max_steps_terminates(
        self, loop: AgentLoop, store: SqliteSessionStore, fake_provider: FakeProvider
    ) -> None:
        tool_responses = [
            LLMResponse(
                tool_calls=[ToolCallRequest(id=f"c{i}", name="utc_time", arguments="{}")],
                finish_reason="tool_calls",
            )
            for i in range(10)
        ]
        fake_provider.set_responses(tool_responses)
        session = Session(id="s1")
        await store.create_session(session)

        run = await loop.run(session, "Keep going")

        assert run.status.value == "timed_out"
        assert fake_provider.call_count == 5

    @pytest.mark.asyncio
    async def test_cancellation(
        self, loop: AgentLoop, store: SqliteSessionStore, fake_provider: FakeProvider
    ) -> None:
        responses = []
        for i in range(5):
            responses.append(LLMResponse(
                tool_calls=[ToolCallRequest(id=f"c{i}", name="utc_time", arguments="{}")],
                finish_reason="tool_calls",
            ))
        fake_provider.set_responses(responses)
        session = Session(id="s1")
        await store.create_session(session)

        import asyncio
        async def delayed_cancel() -> None:
            await asyncio.sleep(0.1)
            loop.cancel()

        task = asyncio.create_task(delayed_cancel())
        run = await loop.run(session, "Start")
        await task

        assert run.status.value in ("cancelled", "timed_out")

    @pytest.mark.asyncio
    async def test_missing_tool_handled(
        self, loop: AgentLoop, store: SqliteSessionStore, fake_provider: FakeProvider
    ) -> None:
        fake_provider.set_responses([
            LLMResponse(
                tool_calls=[ToolCallRequest(id="c1", name="nonexistent", arguments="{}")],
                finish_reason="tool_calls",
            ),
            LLMResponse(content="Tool not found, proceeding.", finish_reason="stop"),
        ])
        session = Session(id="s1")
        await store.create_session(session)

        run = await loop.run(session, "Use missing tool")
        assert run.status.value == "completed"

    @pytest.mark.asyncio
    async def test_run_events_persisted(
        self, loop: AgentLoop, store: SqliteSessionStore, fake_provider: FakeProvider
    ) -> None:
        fake_provider.set_responses([LLMResponse(content="Done", finish_reason="stop")])
        session = Session(id="s1")
        await store.create_session(session)

        run = await loop.run(session, "Hello")

        retrieved = await store.get_run(run.id)
        assert retrieved is not None
        assert retrieved.status.value == "completed"
