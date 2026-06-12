from __future__ import annotations

import pytest

from ya.ports.tools import ToolDefinition
from ya.tools.builtin.utc_time import UtcTimeTool
from ya.tools.policy import PermissionPolicy
from ya.tools.registry import ToolRegistry


class TestToolRegistry:
    @pytest.fixture
    def tool(self) -> UtcTimeTool:
        return UtcTimeTool()

    @pytest.fixture
    def registry(self) -> ToolRegistry:
        return ToolRegistry()

    def test_register_tool(self, registry: ToolRegistry, tool: UtcTimeTool) -> None:
        registry.register(tool)
        entry = registry.get("utc_time")
        assert entry is not None
        assert entry.name == "utc_time"

    def test_register_duplicate_raises(
        self, registry: ToolRegistry, tool: UtcTimeTool
    ) -> None:
        registry.register(tool)
        with pytest.raises(ValueError, match="already registered"):
            registry.register(tool)

    def test_get_nonexistent(self, registry: ToolRegistry) -> None:
        assert registry.get("nonexistent") is None

    def test_list_definitions(self, registry: ToolRegistry, tool: UtcTimeTool) -> None:
        registry.register(tool)
        defs = registry.list_definitions()
        assert len(defs) == 1
        assert defs[0].name == "utc_time"

    def test_list_definitions_excludes_disabled(
        self, registry: ToolRegistry, tool: UtcTimeTool
    ) -> None:
        registry.register(tool)
        registry.disable("utc_time")
        defs = registry.list_definitions(enabled_only=True)
        assert len(defs) == 0

    def test_disable_nonexistent_raises(self, registry: ToolRegistry) -> None:
        with pytest.raises(KeyError):
            registry.disable("nonexistent")

    def test_enable_disabled_tool(self, registry: ToolRegistry, tool: UtcTimeTool) -> None:
        registry.register(tool)
        registry.disable("utc_time")
        registry.enable("utc_time")
        assert registry.get("utc_time").definition.enabled is True  # type: ignore[union-attr]

    @pytest.mark.asyncio
    async def test_execute_tool(self, registry: ToolRegistry, tool: UtcTimeTool) -> None:
        registry.register(tool)
        result = await registry.execute("utc_time", {})
        assert result.success
        assert "T" in result.content

    @pytest.mark.asyncio
    async def test_execute_disabled_raises(
        self, registry: ToolRegistry, tool: UtcTimeTool
    ) -> None:
        registry.register(tool)
        registry.disable("utc_time")
        result = await registry.execute("utc_time", {})
        assert not result.success

    @pytest.mark.asyncio
    async def test_execute_nonexistent_raises(self, registry: ToolRegistry) -> None:
        result = await registry.execute("nonexistent", {})
        assert not result.success


class TestPermissionPolicy:
    @pytest.fixture
    def tool(self) -> UtcTimeTool:
        return UtcTimeTool()

    def test_default_policy_allows_safe(self, tool: UtcTimeTool) -> None:
        policy = PermissionPolicy()
        allowed, reason = policy.authorize(tool, {})
        assert allowed
        assert reason == ""

    def test_default_policy_rejects_dangerous(self) -> None:
        dangerous_def = ToolDefinition(
            name="rm_rf",
            description="Dangerous delete",
            parameters={"type": "object", "properties": {}},
            risk="dangerous",
            enabled=True,
        )

        class DangerousTool:
            definition = dangerous_def
            async def execute(self, arguments): ...

        policy = PermissionPolicy()
        allowed, reason = policy.authorize(DangerousTool(), {})
        assert not allowed
        assert "not allowed" in reason

    def test_policy_disabled_tool_rejected(self, tool: UtcTimeTool) -> None:
        tool.definition.enabled = False
        policy = PermissionPolicy()
        allowed, reason = policy.authorize(tool, {})
        assert not allowed
        assert "disabled" in reason

    def test_policy_allowlist_overrides_risk(self) -> None:
        dangerous_def = ToolDefinition(
            name="rm_rf",
            description="Dangerous delete",
            parameters={"type": "object", "properties": {}},
            risk="dangerous",
            enabled=True,
        )

        class DangerousTool:
            definition = dangerous_def
            async def execute(self, arguments): ...

        policy = PermissionPolicy(allowlist={"rm_rf"})
        allowed, reason = policy.authorize(DangerousTool(), {})
        assert allowed


class TestUtcTimeTool:
    @pytest.mark.asyncio
    async def test_returns_iso_format(self) -> None:
        tool = UtcTimeTool()
        result = await tool.execute({})
        assert result.success
        assert "T" in result.content
        assert "+00:00" in result.content or result.content.endswith("Z")
