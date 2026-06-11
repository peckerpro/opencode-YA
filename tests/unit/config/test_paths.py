from __future__ import annotations

from pathlib import Path

import pytest

from ya.config.paths import resolve_paths
from ya.config.settings import Settings


class TestResolvePaths:
    def test_default_home_structure(self) -> None:
        settings = Settings(ya_home=Path("/tmp/ya-test-home"))
        paths = resolve_paths(settings)
        assert paths.ya_home == Path("/tmp/ya-test-home")
        assert paths.state_db == Path("/tmp/ya-test-home/state/ya.db")
        assert paths.logs == Path("/tmp/ya-test-home/logs")
        assert paths.audit_logs == Path("/tmp/ya-test-home/logs/audit")
        assert paths.memory == Path("/tmp/ya-test-home/memory")

    def test_custom_home_paths_nested_correctly(self) -> None:
        settings = Settings(ya_home=Path("/opt/ya-data"))
        paths = resolve_paths(settings)
        assert paths.rag == Path("/opt/ya-data/rag")
        assert paths.cron == Path("/opt/ya-data/cron")
        assert paths.tmp == Path("/opt/ya-data/tmp")
        assert paths.workspace == Path("/opt/ya-data/workspace")

    def test_paths_are_frozen_dataclass(self) -> None:
        settings = Settings(ya_home=Path("/tmp/ya"))
        paths = resolve_paths(settings)
        with pytest.raises(Exception):  # noqa: B017
            paths.ya_home = Path("/other")  # type: ignore[misc]

    def test_chinese_path(self) -> None:
        settings = Settings(ya_home=Path("/tmp/我的助手"))
        paths = resolve_paths(settings)
        assert "我的助手" in str(paths.ya_home)
        assert "我的助手" in str(paths.logs)
