from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import SecretStr

from ya.config.settings import Settings, load_settings


class TestSettings:
    def test_default_values(self) -> None:
        settings = Settings()
        assert settings.ya_home == Path("~/.ya")
        assert settings.ya_llm_provider == "minimax"
        assert settings.ya_llm_model == "MiniMax-M3"
        assert settings.minimax_api_key is None
        assert settings.minimax_base_url == "https://api.minimaxi.com/v1"

    def test_ya_home_expanded_resolves_tilde(self) -> None:
        settings = Settings(ya_home=Path("~/my-ya"))
        expanded = settings.ya_home_expanded
        assert expanded == Path.home() / "my-ya"

    def test_env_var_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("YA_LLM_MODEL", "MiniMax-M4")
        monkeypatch.setenv("YA_HOME", "/custom/ya/home")
        settings = Settings()
        assert settings.ya_llm_model == "MiniMax-M4"
        assert settings.ya_home == Path("/custom/ya/home")

    def test_secret_fields_are_masked(self) -> None:
        settings = Settings(minimax_api_key=SecretStr("sk-test-key-123"))
        assert settings.minimax_api_key is not None
        assert settings.minimax_api_key.get_secret_value() == "sk-test-key-123"
        assert "sk-test-key-123" not in str(settings.minimax_api_key)
        assert "***" in str(settings.minimax_api_key)

    def test_load_settings_returns_settings_instance(self) -> None:
        settings = load_settings()
        assert isinstance(settings, Settings)

    def test_missing_optional_secret_is_none(self) -> None:
        settings = Settings()
        assert settings.minimax_api_key is None
        assert settings.github_token is None

    def test_extra_env_vars_ignored(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("UNKNOWN_VAR", "should-be-ignored")
        settings = Settings()
        assert not hasattr(settings, "unknown_var")

    def test_chinese_path_resolution(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("YA_HOME", "/tmp/测试目录")
        settings = Settings()
        assert settings.ya_home == Path("/tmp/测试目录")
