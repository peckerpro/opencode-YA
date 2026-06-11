from __future__ import annotations

import pytest

from ya.ports.tools import ToolDefinition
from ya.tools.custom import CircuitBreaker, ConfirmationStore, CustomTool


class TestCircuitBreaker:
    def test_starts_closed(self) -> None:
        cb = CircuitBreaker(failure_threshold=3)
        assert not cb.is_open()
        assert cb.state == "closed"

    def test_opens_after_threshold(self) -> None:
        cb = CircuitBreaker(failure_threshold=2)
        cb.record_failure()
        assert not cb.is_open()
        cb.record_failure()
        assert cb.is_open()

    def test_success_resets(self) -> None:
        cb = CircuitBreaker(failure_threshold=2)
        cb.record_failure()
        cb.record_success()
        cb.record_failure()
        assert not cb.is_open()

    def test_recovery_after_timeout(self) -> None:
        cb = CircuitBreaker(failure_threshold=1, recovery_seconds=0.001)
        cb.record_failure()
        assert cb.is_open()

        import time
        time.sleep(0.01)
        assert not cb.is_open()


class TestCustomTool:
    @pytest.mark.asyncio
    async def test_successful_execution(self) -> None:
        def echo(message: str = "") -> str:
            return f"Echo: {message}"

        tool = CustomTool(
            definition=ToolDefinition(
                name="echo",
                description="Echo test",
                parameters={"type": "object", "properties": {}},
            ),
            handler=echo,
        )

        success, result = await tool.execute({"message": "hello"})
        assert success
        assert "hello" in result

    @pytest.mark.asyncio
    async def test_failed_execution(self) -> None:
        def fail(**kwargs: object) -> str:
            raise ValueError("boom")

        tool = CustomTool(
            definition=ToolDefinition(
                name="failer",
                description="Always fails",
                parameters={"type": "object", "properties": {}},
            ),
            handler=fail,
        )

        success, result = await tool.execute({})
        assert not success
        assert "boom" in result


class TestConfirmationStore:
    def test_request_and_approve(self) -> None:
        store = ConfirmationStore()
        cid = store.request("dangerous_tool", {"path": "/tmp"})
        assert store.approve(cid)
        assert store.is_approved(cid)

    def test_deny(self) -> None:
        store = ConfirmationStore()
        cid = store.request("rm", {})
        assert store.deny(cid)
        assert not store.is_approved(cid)

    def test_invalid_id(self) -> None:
        store = ConfirmationStore()
        assert not store.approve("nonexistent")
