from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from ya.adapters.stores.sqlite import SqliteSessionStore
from ya.adapters.stores.task_files import FileTaskStore
from ya.application.chat import AgentLoop, AgentLoopConfig
from ya.domain.messages.models import LLMResponse, Message, MessageRole
from ya.domain.sessions.models import Session, SessionStatus
from ya.domain.tasks.models import Task, TaskStatus
from ya.ports.tools import ToolDefinition
from ya.tools.builtin.utc_time import UtcTimeTool
from ya.tools.policy import PermissionPolicy
from ya.tools.registry import ToolRegistry

from tests.unit.agents.test_agent_loop import FakeProvider


class TestV01Integration:
    @pytest.mark.asyncio
    async def test_full_session_lifecycle(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ya-integration-") as tmp:
            tmp_path = Path(tmp)

            store = SqliteSessionStore(tmp_path / "ya.db")
            await store.initialize()

            session = Session(id="s1", title="Integration Test")
            await store.create_session(session)

            retrieved = await store.get_session("s1")
            assert retrieved is not None
            assert retrieved.title == "Integration Test"

            sessions = await store.list_sessions()
            assert len(sessions) == 1

            await store.close()

            store2 = SqliteSessionStore(tmp_path / "ya.db")
            await store2.initialize()

            restored = await store2.get_session("s1")
            assert restored is not None
            assert restored.title == "Integration Test"

            await store2.close()

    @pytest.mark.asyncio
    async def test_agent_loop_to_task_flow(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ya-flow-") as tmp:
            tmp_path = Path(tmp)

            store = SqliteSessionStore(tmp_path / "ya.db")
            await store.initialize()

            registry = ToolRegistry()
            registry.register(UtcTimeTool())

            policy = PermissionPolicy()

            fake_provider = FakeProvider()
            fake_provider.set_responses([
                LLMResponse(content="Task created successfully.", finish_reason="stop"),
            ])

            loop = AgentLoop(
                provider=fake_provider,
                store=store,
                registry=registry,
                policy=policy,
                config=AgentLoopConfig(max_steps=3),
            )

            session = Session(id="s1", title="Development Session")
            await store.create_session(session)

            run = await loop.run(session, "Create a new task for testing")
            assert run.status.value == "completed"

            messages = await store.get_messages("s1")
            assert len(messages) >= 2
            assert messages[1].content == "Task created successfully."

            task_store = FileTaskStore(tmp_path / "workspace")
            task_store.initialize()

            task = Task(id="T-001", title="Test task", status=TaskStatus.READY)
            task_store.save_task(task)

            claimed = task_store.claim_task("T-001", "agent:coding/test")
            assert claimed.status == TaskStatus.IN_PROGRESS

            task_store.transition_task("T-001", TaskStatus.REVIEW)
            task_store.transition_task("T-001", TaskStatus.TESTING)
            finalized = task_store.transition_task("T-001", TaskStatus.DONE)
            assert finalized.status == TaskStatus.DONE
            assert finalized.completed_at is not None

            events = task_store.read_events("T-001")
            assert len(events) >= 3

            await store.close()

    @pytest.mark.asyncio
    async def test_chinese_utf8_end_to_end(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ya-utf8-") as tmp:
            tmp_path = Path(tmp)

            store = SqliteSessionStore(tmp_path / "ya.db")
            await store.initialize()

            session = Session(id="会话-001", title="中文集成测试")
            await store.create_session(session)

            msg = Message(role=MessageRole.USER, content="你好，世界！", tool_call_id="m1")
            await store.append_message("会话-001", msg)

            messages = await store.get_messages("会话-001")
            assert len(messages) == 1
            assert messages[0].content == "你好，世界！"

            task_store = FileTaskStore(tmp_path / "workspace")
            task_store.initialize()

            task = Task(id="任务-001", title="中文任务", status=TaskStatus.READY)
            task_store.save_task(task)
            loaded = task_store.load_task("任务-001")
            assert loaded is not None
            assert loaded.title == "中文任务"

            await store.close()
