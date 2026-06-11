from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from ya.adapters.git.sync import GitSyncBackend


class TestGitSyncBackend:
    @pytest.fixture
    def repo_path(self) -> Path:
        with tempfile.TemporaryDirectory(prefix="ya-git-test-") as tmp:
            yield Path(tmp)

    @pytest.mark.asyncio
    async def test_status_clean_repo(self, repo_path: Path) -> None:
        import subprocess
        subprocess.run(["git", "init"], cwd=repo_path, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo_path, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=repo_path, capture_output=True)
        (repo_path / "test.txt").write_text("hello")
        subprocess.run(["git", "add", "-A"], cwd=repo_path, capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=repo_path, capture_output=True)

        sync = GitSyncBackend(repo_path)
        status = await sync.status()
        assert status["status"] == "clean"

    @pytest.mark.asyncio
    async def test_status_dirty_repo(self, repo_path: Path) -> None:
        import subprocess
        subprocess.run(["git", "init"], cwd=repo_path, capture_output=True)
        (repo_path / "untracked.txt").write_text("new file")

        sync = GitSyncBackend(repo_path)
        status = await sync.status()
        assert status["status"] == "dirty"
