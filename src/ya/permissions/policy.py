from __future__ import annotations

from ya.permissions.models import (
    CAPABILITIES,
    Capability,
    Permission,
    PermissionDecision,
    PermissionEffect,
    Scope,
)


class PermissionPolicy:
    def __init__(self) -> None:
        self._rules: list[Permission] = []
        self._capabilities: dict[str, Capability] = {
            k: Capability(name=k, description=v) for k, v in CAPABILITIES.items()
        }

    def add_rule(self, permission: Permission) -> None:
        self._rules.append(permission)

    def remove_rule(self, permission_id: str) -> None:
        self._rules = [r for r in self._rules if r.id != permission_id]

    def evaluate(
        self,
        capability: str,
        scope: Scope,
        role: str = "",
    ) -> PermissionDecision:
        matching = [r for r in self._rules if r.capability == capability]
        if not matching:
            return PermissionDecision(allowed=True, reason=f"No rule for {capability}")

        for rule in matching:
            if rule.effect == PermissionEffect.DENY:
                return PermissionDecision(
                    allowed=False,
                    reason=f"Explicit deny: {rule.reason}",
                    matched_rule_id=rule.id,
                )

        for rule in matching:
            if rule.effect == PermissionEffect.CONFIRM:
                return PermissionDecision(
                    allowed=True,
                    requires_confirmation=True,
                    reason="Confirmation required",
                    matched_rule_id=rule.id,
                )

        for rule in matching:
            if rule.effect == PermissionEffect.ALLOW:
                return PermissionDecision(
                    allowed=True,
                    reason=f"Allowed by rule: {rule.reason}",
                    matched_rule_id=rule.id,
                )

        return PermissionDecision(allowed=False, reason="No matching allow rule")


class PermissionGuard:
    def __init__(self, policy: PermissionPolicy) -> None:
        self._policy = policy

    async def check(
        self,
        capability: str,
        scope: Scope,
        role: str = "",
    ) -> PermissionDecision:
        return self._policy.evaluate(capability, scope, role)
