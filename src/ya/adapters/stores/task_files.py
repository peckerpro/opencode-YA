from __future__ import annotations

import json
import os
from pathlib import Path

from ya.domain.tasks.models import Task, TaskEvent, TaskStatus


class FileTaskStore:
    def __init__(self, workspace_path: Path) -> None:
        self._workspace = workspace_path
        self._tasks_dir = workspace_path / "tasks"
        self._events_path = workspace_path / "events.jsonl"
        self._lock_dir = workspace_path / "locks"

    def initialize(self) -> None:
        self._tasks_dir.mkdir(parents=True, exist_ok=True)
        self._lock_dir.mkdir(parents=True, exist_ok=True)

    def save_task(self, task: Task) -> None:
        path = self._tasks_dir / f"{task.id}.json"
        path.write_text(task.model_dump_json(indent=2), encoding="utf-8")

    def load_task(self, task_id: str) -> Task | None:
        path = self._tasks_dir / f"{task_id}.json"
        if not path.exists():
            return None
        return Task.model_validate_json(path.read_text(encoding="utf-8"))

    def list_tasks(self) -> list[Task]:
        tasks: list[Task] = []
        if not self._tasks_dir.exists():
            return tasks
        for f in sorted(self._tasks_dir.glob("*.json")):
            data = json.loads(f.read_text(encoding="utf-8"))
            tasks.append(Task.model_validate(data))
        return tasks

    def append_event(self, event: TaskEvent) -> None:
        line = event.model_dump_json() + "\n"
        with open(self._events_path, "a", encoding="utf-8") as f:
            f.write(line)

    def claim_task(self, task_id: str, owner: str) -> Task:
        lock_path = self._lock_dir / f"{task_id}.lock"
        try:
            fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
        except FileExistsError:
            raise RuntimeError(f"Task '{task_id}' is already claimed") from None

        task = self.load_task(task_id)
        if task is None:
            os.unlink(lock_path)
            raise KeyError(f"Task '{task_id}' not found")
        if task.status != TaskStatus.READY:
            os.unlink(lock_path)
            raise ValueError(f"Task '{task_id}' is not Ready (current: {task.status.value})")

        task.owner = owner
        task.transition_to(TaskStatus.IN_PROGRESS)
        self.save_task(task)

        lock_path.write_text(
            json.dumps({"owner": owner, "acquired_at": task.updated_at}),
            encoding="utf-8",
        )
        self.append_event(TaskEvent(
            task_id=task_id,
            event_type="claimed",
            owner=owner,
            previous_status=TaskStatus.READY.value,
            new_status=TaskStatus.IN_PROGRESS.value,
        ))
        return task

    def release_task(self, task_id: str) -> None:
        lock_path = self._lock_dir / f"{task_id}.lock"
        if lock_path.exists():
            lock_path.unlink()

    def transition_task(
        self,
        task_id: str,
        new_status: TaskStatus,
        blocked_reason: str = "",
    ) -> Task:
        task = self.load_task(task_id)
        if task is None:
            raise KeyError(f"Task '{task_id}' not found")

        previous = task.status
        if blocked_reason:
            task.blocked_reason = blocked_reason
        task.transition_to(new_status)
        self.save_task(task)

        if new_status in (TaskStatus.DONE, TaskStatus.BLOCKED):
            self.release_task(task_id)

        self.append_event(TaskEvent(
            task_id=task_id,
            event_type="transition",
            owner=task.owner,
            previous_status=previous.value,
            new_status=new_status.value,
            reason=blocked_reason,
        ))
        return task

    def read_events(self, task_id: str | None = None) -> list[TaskEvent]:
        events: list[TaskEvent] = []
        if not self._events_path.exists():
            return events
        for line in self._events_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            event = TaskEvent.model_validate_json(line)
            if task_id is None or event.task_id == task_id:
                events.append(event)
        return events
