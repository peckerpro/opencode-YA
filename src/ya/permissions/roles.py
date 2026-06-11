from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RoleProfile:
    name: str
    role_class: str
    capabilities: set[str] = field(default_factory=set)
    restrictions: set[str] = field(default_factory=set)
    default_scope: str = "session"


ROLE_PROFILES: dict[str, RoleProfile] = {
    "planner": RoleProfile(
        name="Planner",
        role_class="project",
        capabilities={
            "task.read", "task.transition",
            "workspace.read",
            "memory.read",
        },
        restrictions={"workspace.write", "tool.execute.dangerous"},
    ),
    "coding": RoleProfile(
        name="Coding Agent",
        role_class="project",
        capabilities={
            "task.read", "task.transition",
            "workspace.read", "workspace.write",
            "tool.execute.safe",
            "memory.read",
        },
        restrictions={"memory.write", "git.push", "tool.execute.dangerous"},
    ),
    "review": RoleProfile(
        name="Review Agent",
        role_class="project",
        capabilities={
            "task.read", "task.transition",
            "workspace.read",
            "memory.read",
        },
        restrictions={"workspace.write", "tool.execute.dangerous"},
    ),
    "test": RoleProfile(
        name="Test Agent",
        role_class="project",
        capabilities={
            "task.read", "task.transition",
            "workspace.read", "workspace.write",
            "tool.execute.safe", "tool.execute.guarded",
            "memory.read",
        },
        restrictions={"memory.write", "git.push"},
    ),
    "document": RoleProfile(
        name="Document Agent",
        role_class="project",
        capabilities={
            "task.read", "task.transition",
            "workspace.read", "workspace.write",
            "memory.read", "memory.write",
        },
        restrictions={"tool.execute.dangerous", "git.push"},
    ),
    "coordinator": RoleProfile(
        name="Coordinator",
        role_class="project",
        capabilities={
            "task.read", "task.transition",
            "workspace.read",
            "agent.list",
            "project.team.start",
        },
        restrictions={
            "workspace.write", "memory.write",
            "session.pause", "session.resume",
            "session.archive", "session.close",
        },
    ),
    "root": RoleProfile(
        name="Root Agent",
        role_class="root",
        capabilities={
            "session.list", "session.inspect", "session.summarize",
            "session.search", "session.instruction.send",
            "session.spawn", "session.pause", "session.resume",
            "session.archive", "session.close",
            "agent.list", "system.status.read",
            "project.create", "project.team.start",
            "memory.read", "memory.write", "memory.sync",
            "rag.query", "rag.reindex",
            "cron.read", "cron.manage",
            "audit.read",
        },
        restrictions={"tool.execute.dangerous"},
    ),
}


def get_role_profile(role_name: str) -> RoleProfile | None:
    return ROLE_PROFILES.get(role_name)
