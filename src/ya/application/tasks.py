from __future__ import annotations

from pathlib import Path

from ya.adapters.stores.task_files import FileTaskStore
from ya.domain.tasks.models import Task, TaskEvent, TaskStatus


class TaskService:
    def __init__(self, workspace_path: Path) -> None:
        self._store = FileTaskStore(workspace_path)

    def initialize(self) -> None:
        self._store.initialize()

    def create_task(self, task: Task) -> Task:
        existing = self._store.load_task(task.id)
        if existing is not None:
            raise ValueError(f"Task '{task.id}' already exists")
        self._store.save_task(task)
        self._store.append_event(TaskEvent(
            task_id=task.id,
            event_type="created",
            new_status=task.status.value,
        ))
        return task

    def get_task(self, task_id: str) -> Task | None:
        return self._store.load_task(task_id)

    def list_tasks(self, status: TaskStatus | None = None) -> list[Task]:
        tasks = self._store.list_tasks()
        if status is not None:
            tasks = [t for t in tasks if t.status == status]
        return tasks

    def claim_task(self, task_id: str, owner: str) -> Task:
        return self._store.claim_task(task_id, owner)

    def transition_task(
        self,
        task_id: str,
        new_status: TaskStatus,
        blocked_reason: str = "",
    ) -> Task:
        return self._store.transition_task(task_id, new_status, blocked_reason)

    def get_events(self, task_id: str | None = None) -> list[TaskEvent]:
        return self._store.read_events(task_id)
