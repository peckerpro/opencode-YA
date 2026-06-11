from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from ya.domain.tasks.models import Task


class AgentLifecycle(StrEnum):
    IDLE = "idle"
    WORKING = "working"
    WAITING = "waiting"


class TeamAgent(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:8])
    role: str = ""
    status: AgentLifecycle = AgentLifecycle.IDLE
    current_task_id: str = ""
    heartbeat_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class Coordinator:
    def __init__(self) -> None:
        self._agents: dict[str, TeamAgent] = {}
        self._task_assignments: dict[str, str] = {}
        self._events: list[dict[str, object]] = []

    def register_agent(self, role: str) -> TeamAgent:
        agent = TeamAgent(role=role)
        self._agents[agent.id] = agent
        self._log_event("agent_registered", {"agent_id": agent.id, "role": role})
        return agent

    def assign_task(self, task: Task, agent_id: str) -> bool:
        agent = self._agents.get(agent_id)
        if agent is None:
            return False
        if agent.status != AgentLifecycle.IDLE:
            return False
        if task.id in self._task_assignments:
            return False

        agent.status = AgentLifecycle.WORKING
        agent.current_task_id = task.id
        self._task_assignments[task.id] = agent_id
        self._log_event("task_assigned", {"task_id": task.id, "agent_id": agent_id})
        return True

    def release_task(self, task_id: str) -> bool:
        agent_id = self._task_assignments.pop(task_id, None)
        if agent_id:
            agent = self._agents.get(agent_id)
            if agent:
                agent.status = AgentLifecycle.IDLE
                agent.current_task_id = ""
            self._log_event("task_released", {"task_id": task_id, "agent_id": agent_id})
            return True
        return False

    def heartbeat(self, agent_id: str) -> bool:
        agent = self._agents.get(agent_id)
        if agent is None:
            return False
        agent.heartbeat_at = datetime.now(UTC).isoformat()
        return True

    def get_idle_agents(self) -> list[TeamAgent]:
        return [a for a in self._agents.values() if a.status == AgentLifecycle.IDLE]

    def get_agent(self, agent_id: str) -> TeamAgent | None:
        return self._agents.get(agent_id)

    def get_task_owner(self, task_id: str) -> str | None:
        return self._task_assignments.get(task_id)

    def _log_event(self, event_type: str, data: dict[str, object]) -> None:
        self._events.append({
            "event_type": event_type,
            "timestamp": datetime.now(UTC).isoformat(),
            **data,
        })

    def get_events(self) -> list[dict[str, object]]:
        return list(self._events)

    def get_status(self) -> dict[str, object]:
        return {
            "total_agents": len(self._agents),
            "idle_agents": len(self.get_idle_agents()),
            "assigned_tasks": len(self._task_assignments),
            "roles": list({a.role for a in self._agents.values()}),
        }
