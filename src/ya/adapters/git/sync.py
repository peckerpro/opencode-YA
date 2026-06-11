from __future__ import annotations

import asyncio
from pathlib import Path


class GitSyncBackend:
    def __init__(self, repo_path: Path, remote: str = "origin", branch: str = "master") -> None:
        self._repo = repo_path
        self._remote = remote
        self._branch = branch

    async def _run(self, *args: str) -> str:
        proc = await asyncio.create_subprocess_exec(
            "git", *args,
            cwd=str(self._repo),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(stderr.decode() if stderr else f"git {' '.join(args)} failed")
        return stdout.decode().strip()

    async def status(self) -> dict[str, str]:
        try:
            output = await self._run("status", "--short")
            return {"status": "dirty" if output else "clean", "changes": output}
        except Exception:
            return {"status": "error"}

    async def pull(self) -> str:
        return await self._run("pull", "--rebase", self._remote, self._branch)

    async def commit_and_push(self, message: str) -> str:
        await self._run("add", "-A")
        await self._run("commit", "-m", message)
        return await self._run("push", self._remote, self._branch)
