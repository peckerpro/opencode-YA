from __future__ import annotations

import pytest

from ya.permissions.audit import AuditEvent, AuditStore
from ya.permissions.models import Permission, PermissionEffect, Scope
from ya.permissions.policy import PermissionGuard, PermissionPolicy
from ya.permissions.roles import get_role_profile


class TestPermissionPolicy:
    @pytest.fixture
    def policy(self) -> PermissionPolicy:
        return PermissionPolicy()

    def test_no_rules_allows(self, policy: PermissionPolicy) -> None:
        decision = policy.evaluate("task.read", Scope())
        assert decision.allowed

    def test_explicit_deny(self, policy: PermissionPolicy) -> None:
        policy.add_rule(Permission(
            id="r1", capability="git.push",
            effect=PermissionEffect.DENY, reason="No push allowed",
        ))
        decision = policy.evaluate("git.push", Scope())
        assert not decision.allowed
        assert "Explicit deny" in decision.reason

    def test_confirm_requires_confirmation(self, policy: PermissionPolicy) -> None:
        policy.add_rule(Permission(
            id="r1", capability="session.spawn",
            effect=PermissionEffect.CONFIRM, reason="Needs approval",
        ))
        decision = policy.evaluate("session.spawn", Scope())
        assert decision.allowed
        assert decision.requires_confirmation

    def test_deny_takes_priority(self, policy: PermissionPolicy) -> None:
        policy.add_rule(Permission(id="r1", capability="memory.sync", effect=PermissionEffect.DENY))
        policy.add_rule(Permission(id="r2", capability="memory.sync", effect=PermissionEffect.ALLOW))
        decision = policy.evaluate("memory.sync", Scope())
        assert not decision.allowed


class TestPermissionGuard:
    def test_guard_uses_policy(self) -> None:
        policy = PermissionPolicy()
        guard = PermissionGuard(policy)

        import asyncio
        decision = asyncio.run(guard.check("task.read", Scope(), "coding"))
        assert decision.allowed

    def test_guard_denies_git_push_for_coding(self) -> None:
        policy = PermissionPolicy()
        policy.add_rule(Permission(
            id="r1", capability="git.push",
            effect=PermissionEffect.DENY, reason="Coding cannot push",
        ))
        guard = PermissionGuard(policy)

        import asyncio
        decision = asyncio.run(guard.check("git.push", Scope(), "coding"))
        assert not decision.allowed


class TestAuditStore:
    def test_append_and_query(self) -> None:
        store = AuditStore()
        store.append(AuditEvent(capability="task.read", actor_agent_id="a1"))
        store.append(AuditEvent(capability="git.push", actor_agent_id="a2"))

        assert store.count() == 2

        results = store.query(capability="git.push")
        assert len(results) == 1
        assert results[0].actor_agent_id == "a2"

    def test_query_limit(self) -> None:
        store = AuditStore()
        for i in range(5):
            store.append(AuditEvent(capability="cron.manage", actor_agent_id=f"a{i}"))
        results = store.query(limit=3)
        assert len(results) == 3


class TestRoleProfiles:
    def test_coding_role_restrictions(self) -> None:
        role = get_role_profile("coding")
        assert role is not None
        assert "git.push" in role.restrictions
        assert "memory.write" in role.restrictions
        assert "task.read" in role.capabilities

    def test_root_role_has_session_control(self) -> None:
        role = get_role_profile("root")
        assert role is not None
        assert "session.spawn" in role.capabilities
        assert "session.pause" in role.capabilities
        assert "audit.read" in role.capabilities

    def test_coordinator_cannot_write_workspace(self) -> None:
        role = get_role_profile("coordinator")
        assert role is not None
        assert "workspace.write" in role.restrictions

    def test_nonexistent_role(self) -> None:
        assert get_role_profile("nonexistent") is None
