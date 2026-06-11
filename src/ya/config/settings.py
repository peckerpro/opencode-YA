from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    ya_home: Path = Path("~/.ya")

    ya_llm_provider: Literal["minimax"] = "minimax"
    ya_llm_model: str = "MiniMax-M3"

    minimax_api_key: SecretStr | None = None
    minimax_base_url: str = "https://api.minimaxi.com/v1"

    mineru_api_key: SecretStr | None = None

    github_token: SecretStr | None = None

    @property
    def ya_home_expanded(self) -> Path:
        return self.ya_home.expanduser().resolve()


def load_settings() -> Settings:
    return Settings()
