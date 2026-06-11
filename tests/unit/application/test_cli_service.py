from __future__ import annotations

from ya.application.cli_service import CLIService


class TestCLIService:
    def test_missing_api_key(self) -> None:
        import asyncio
        async def _test() -> None:
            service = CLIService()
            result = await service.run_prompt("hello")
            assert "error" in result
        asyncio.run(_test())
