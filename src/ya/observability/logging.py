from __future__ import annotations

import logging
import sys
from collections.abc import Sequence

_YA_LOGGER_NAME = "ya"
_SECRET_PLACEHOLDER = "***"

_REDACT_PATTERNS: Sequence[str] = (
    "api_key",
    "token",
    "secret",
    "password",
    "credential",
    "authorization",
)


class _SecretRedactingFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        lower = message.lower()
        for pattern in _REDACT_PATTERNS:
            if pattern in lower:
                message = "[REDACTED]"
                break
        return message


def configure_logging(level: int = logging.INFO) -> None:
    logger = logging.getLogger(_YA_LOGGER_NAME)
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setLevel(level)

        formatter = _SecretRedactingFormatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%SZ",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.propagate = False


def get_logger(name: str | None = None) -> logging.Logger:
    if name is None:
        return logging.getLogger(_YA_LOGGER_NAME)
    return logging.getLogger(f"{_YA_LOGGER_NAME}.{name}")
