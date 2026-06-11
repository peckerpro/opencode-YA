from __future__ import annotations

import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_home() -> Path:
    with tempfile.TemporaryDirectory(prefix="ya-test-") as tmp:
        yield Path(tmp)
