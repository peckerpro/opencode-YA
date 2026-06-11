from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from ya.adapters.stores.sqlite import SqliteSessionStore
from ya.domain.agents.models import AgentEvent, Run, RunStatus
from ya.domain.messages.models import Message, MessageRole
from ya.domain.sessions.models import Session, SessionStatus


@pytest.fixture
async def store() -> SqliteSessionStore:
    with tempfile.TemporaryDirectory(prefix="ya-test-db-") as tmp:
        db_path = Path(tmp) / "ya.db"
        s = SqliteSessionStore(db_path)
        await s.initialize()
        yield s
        await s.close()


class TestSqliteSessionStore:
    @pytest.mark.asyncio
    async def test_initialize_creates_db(self, store: SqliteSessionStore) -> None:
        assert store._conn is not None

    @pytest.mark.asyncio
    async def test_create_and_get_session(self, store: SqliteSessionStore) -> None:
        session = Session(
            id="s1",
            title="Test Session",
            status=SessionStatus.ACTIVE,
        )
        await store.create_session(session)

        retrieved = await store.get_session("s1")
        assert retrieved is not None
        assert retrieved.title == "Test Session"
        assert retrieved.status == SessionStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_get_nonexistent_session(self, store: SqliteSessionStore) -> None:
        result = await store.get_session("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_list_sessions(self, store: SqliteSessionStore) -> None:
        await store.create_session(Session(id="s1", title="First"))
        await store.create_session(Session(id="s2", title="Second"))

        sessions = await store.list_sessions()
        assert len(sessions) == 2
        titles = {s.title for s in sessions}
        assert titles == {"First", "Second"}

    @pytest.mark.asyncio
    async def test_update_session(self, store: SqliteSessionStore) -> None:
        session = Session(id="s1", title="Original")
        await store.create_session(session)

        session.title = "Updated"
        session.status = SessionStatus.PAUSED
        await store.update_session(session)

        retrieved = await store.get_session("s1")
        assert retrieved is not None
        assert retrieved.title == "Updated"
        assert retrieved.status == SessionStatus.PAUSED

    @pytest.mark.asyncio
    async def test_append_and_get_messages(self, store: SqliteSessionStore) -> None:
        await store.create_session(Session(id="s1"))

        msg1 = Message(role=MessageRole.USER, content="Hello", tool_call_id="m1")
        msg2 = Message(role=MessageRole.ASSISTANT, content="Hi there", tool_call_id="m2")

        await store.append_message("s1", msg1)
        await store.append_message("s1", msg2)

        messages = await store.get_messages("s1")
        assert len(messages) == 2
        assert messages[0].role == MessageRole.USER
        assert messages[0].content == "Hello"
        assert messages[1].role == MessageRole.ASSISTANT
        assert messages[1].content == "Hi there"

    @pytest.mark.asyncio
    async def test_chinese_content(self, store: SqliteSessionStore) -> None:
        await store.create_session(Session(id="s1", title="中文会话"))
        msg = Message(role=MessageRole.USER, content="你好世界", tool_call_id="m1")
        await store.append_message("s1", msg)

        messages = await store.get_messages("s1")
        assert len(messages) == 1
        assert messages[0].content == "你好世界"

    @pytest.mark.asyncio
    async def test_create_and_get_run(self, store: SqliteSessionStore) -> None:
        await store.create_session(Session(id="s1"))
        run = Run(id="r1", session_id="s1", agent_id="a1", role_id="role1")

        await store.create_run(run)
        retrieved = await store.get_run("r1")
        assert retrieved is not None
        assert retrieved.status == RunStatus.PENDING

    @pytest.mark.asyncio
    async def test_update_run_status(self, store: SqliteSessionStore) -> None:
        await store.create_session(Session(id="s1"))
        run = Run(id="r1", session_id="s1")
        await store.create_run(run)

        run.status = RunStatus.COMPLETED
        await store.update_run(run)

        retrieved = await store.get_run("r1")
        assert retrieved is not None
        assert retrieved.status == RunStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_append_event(self, store: SqliteSessionStore) -> None:
        await store.create_session(Session(id="s1"))
        run = Run(id="r1", session_id="s1")
        await store.create_run(run)

        event = AgentEvent(id="e1", run_id="r1", event_type="tool_call", payload="{}")
        await store.append_event("r1", event)

    @pytest.mark.asyncio
    async def test_get_nonexistent_run(self, store: SqliteSessionStore) -> None:
        result = await store.get_run("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_empty_session_no_messages(self, store: SqliteSessionStore) -> None:
        await store.create_session(Session(id="s1"))
        messages = await store.get_messages("s1")
        assert messages == []
