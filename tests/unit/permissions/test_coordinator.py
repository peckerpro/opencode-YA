from __future__ import annotations

import pytest

from ya.domain.tasks.models import Task, TaskStatus
from ya.permissions.coordinator import Coordinator


class TestCoordinator:
    @pytest.fixture
    def coordinator(self) -> Coordinator:
        return Coordinator()

    def test_register_agent(self, coordinator: Coordinator) -> None:
        agent = coordinator.register_agent("coding")
        assert agent.role == "coding"

    def test_assign_task_to_idle_agent(self, coordinator: Coordinator) -> None:
        agent = coordinator.register_agent("coding")
        task = Task(id="t1", status=TaskStatus.READY)

        assert coordinator.assign_task(task, agent.id)
        assert coordinator.get_task_owner("t1") == agent.id

    def test_cannot_assign_to_busy_agent(self, coordinator: Coordinator) -> None:
        agent = coordinator.register_agent("coding")
        task1 = Task(id="t1", status=TaskStatus.READY)
        task2 = Task(id="t2", status=TaskStatus.READY)

        assert coordinator.assign_task(task1, agent.id)
        assert not coordinator.assign_task(task2, agent.id)

    def test_release_task_frees_agent(self, coordinator: Coordinator) -> None:
        agent = coordinator.register_agent("coding")
        task = Task(id="t1", status=TaskStatus.READY)
        coordinator.assign_task(task, agent.id)

        assert coordinator.release_task("t1")
        assert coordinator.get_task_owner("t1") is None
        assert coordinator.get_agent(agent.id).status.value == "idle"

    def test_duplicate_task_assignment_prevented(self, coordinator: Coordinator) -> None:
        a1 = coordinator.register_agent("coding")
        a2 = coordinator.register_agent("review")
        task = Task(id="t1", status=TaskStatus.READY)

        assert coordinator.assign_task(task, a1.id)
        assert not coordinator.assign_task(task, a2.id)

    def test_heartbeat_updates_timestamp(self, coordinator: Coordinator) -> None:
        agent = coordinator.register_agent("coding")
        assert coordinator.heartbeat(agent.id)

    def test_get_idle_agents(self, coordinator: Coordinator) -> None:
        a1 = coordinator.register_agent("coding")
        a2 = coordinator.register_agent("review")

        task = Task(id="t1", status=TaskStatus.READY)
        coordinator.assign_task(task, a1.id)

        idle = coordinator.get_idle_agents()
        assert len(idle) == 1
        assert idle[0].id == a2.id

    def test_coordinator_status(self, coordinator: Coordinator) -> None:
        coordinator.register_agent("coding")
        coordinator.register_agent("review")

        status = coordinator.get_status()
        assert status["total_agents"] == 2
        assert status["idle_agents"] == 2

    def test_events_tracked(self, coordinator: Coordinator) -> None:
        agent = coordinator.register_agent("coding")
        task = Task(id="t1", status=TaskStatus.READY)
        coordinator.assign_task(task, agent.id)

        events = coordinator.get_events()
        assert len(events) >= 2

    def test_nonexistent_agent(self, coordinator: Coordinator) -> None:
        assert coordinator.get_agent("nonexistent") is None
        assert not coordinator.heartbeat("nonexistent")
