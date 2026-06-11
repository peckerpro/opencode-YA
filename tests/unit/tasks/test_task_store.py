from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from ya.adapters.stores.task_files import FileTaskStore
from ya.domain.tasks.models import Task, TaskStatus


@pytest.fixture
def workspace() -> Path:
    with tempfile.TemporaryDirectory(prefix="ya-test-workspace-") as tmp:
        yield Path(tmp)


@pytest.fixture
def store(workspace: Path) -> FileTaskStore:
    s = FileTaskStore(workspace)
    s.initialize()
    return s


class TestFileTaskStore:
    def test_initialize_creates_dirs(self, workspace: Path) -> None:
        s = FileTaskStore(workspace / "sub")
        s.initialize()
        assert (workspace / "sub" / "tasks").is_dir()
        assert (workspace / "sub" / "locks").is_dir()

    def test_save_and_load_task(self, store: FileTaskStore) -> None:
        task = Task(id="YA-001", title="Test task", status=TaskStatus.READY)
        store.save_task(task)

        loaded = store.load_task("YA-001")
        assert loaded is not None
        assert loaded.title == "Test task"
        assert loaded.status == TaskStatus.READY

    def test_load_nonexistent_task(self, store: FileTaskStore) -> None:
        assert store.load_task("nonexistent") is None

    def test_list_tasks(self, store: FileTaskStore) -> None:
        store.save_task(Task(id="t1", title="First"))
        store.save_task(Task(id="t2", title="Second"))

        tasks = store.list_tasks()
        assert len(tasks) == 2
        assert {t.title for t in tasks} == {"First", "Second"}

    def test_list_tasks_empty(self, store: FileTaskStore) -> None:
        assert store.list_tasks() == []

    def test_claim_task_success(self, store: FileTaskStore) -> None:
        store.save_task(Task(id="t1", status=TaskStatus.READY))
        task = store.claim_task("t1", "agent-1")

        assert task.owner == "agent-1"
        assert task.status == TaskStatus.IN_PROGRESS

    def test_claim_already_claimed_raises(self, store: FileTaskStore) -> None:
        store.save_task(Task(id="t1", status=TaskStatus.READY))
        store.claim_task("t1", "agent-1")

        with pytest.raises(RuntimeError, match="already claimed"):
            store.claim_task("t1", "agent-2")

    def test_claim_not_ready_raises(self, store: FileTaskStore) -> None:
        store.save_task(Task(id="t1", status=TaskStatus.BACKLOG))
        with pytest.raises(ValueError, match="not Ready"):
            store.claim_task("t1", "agent-1")

    def test_claim_nonexistent_raises(self, store: FileTaskStore) -> None:
        with pytest.raises(KeyError):
            store.claim_task("nonexistent", "agent-1")

    def test_transition_valid(self, store: FileTaskStore) -> None:
        store.save_task(Task(id="t1", status=TaskStatus.READY))
        task = store.transition_task("t1", TaskStatus.IN_PROGRESS)
        assert task.status == TaskStatus.IN_PROGRESS

    def test_transition_invalid_raises(self, store: FileTaskStore) -> None:
        store.save_task(Task(id="t1", status=TaskStatus.READY))
        with pytest.raises(ValueError, match="Invalid transition"):
            store.transition_task("t1", TaskStatus.DONE)

    def test_blocked_requires_reason(self, store: FileTaskStore) -> None:
        store.save_task(Task(id="t1", status=TaskStatus.READY))
        with pytest.raises(ValueError, match="Blocked reason"):
            store.transition_task("t1", TaskStatus.BLOCKED)

    def test_blocked_with_reason(self, store: FileTaskStore) -> None:
        store.save_task(Task(id="t1", status=TaskStatus.READY))
        task = store.transition_task("t1", TaskStatus.BLOCKED, blocked_reason="Waiting for deps")
        assert task.status == TaskStatus.BLOCKED
        assert task.blocked_reason == "Waiting for deps"

    def test_done_sets_completed_at(self, store: FileTaskStore) -> None:
        store.save_task(Task(id="t1", status=TaskStatus.READY))
        store.transition_task("t1", TaskStatus.IN_PROGRESS)
        store.transition_task("t1", TaskStatus.REVIEW)
        store.transition_task("t1", TaskStatus.TESTING)
        task = store.transition_task("t1", TaskStatus.DONE)

        assert task.status == TaskStatus.DONE
        assert task.completed_at is not None

    def test_events_appended(self, store: FileTaskStore) -> None:
        store.save_task(Task(id="t1", status=TaskStatus.READY))
        store.claim_task("t1", "agent-1")

        events = store.read_events("t1")
        assert len(events) >= 1
        assert events[-1].event_type == "claimed"

    def test_events_filter_by_task(self, store: FileTaskStore) -> None:
        store.save_task(Task(id="t1", status=TaskStatus.READY))
        store.save_task(Task(id="t2", status=TaskStatus.READY))
        store.claim_task("t1", "agent-1")

        events_t1 = store.read_events("t1")
        assert len(events_t1) >= 1

    def test_chinese_task_title(self, store: FileTaskStore) -> None:
        task = Task(id="测试-001", title="中文任务标题", status=TaskStatus.READY)
        store.save_task(task)
        loaded = store.load_task("测试-001")
        assert loaded is not None
        assert loaded.title == "中文任务标题"

    def test_release_task_removes_lock(self, store: FileTaskStore) -> None:
        store.save_task(Task(id="t1", status=TaskStatus.READY))
        store.claim_task("t1", "agent-1")
        store.release_task("t1")

        t = store.load_task("t1")
        assert t is not None
        t.status = TaskStatus.READY
        store.save_task(t)

        task = store.claim_task("t1", "agent-2")
        assert task.owner == "agent-2"
