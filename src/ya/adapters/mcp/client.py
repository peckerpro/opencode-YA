from __future__ import annotations

import asyncio
import json
import uuid


class MCPClient:
    def __init__(self, command: list[str], env: dict[str, str] | None = None) -> None:
        self._command = command
        self._env = env
        self._proc: asyncio.subprocess.Process | None = None
        self._pending: dict[str, asyncio.Future[dict[str, object]]] = {}
        self._reader_task: asyncio.Task[None] | None = None

    async def connect(self) -> None:
        self._proc = await asyncio.create_subprocess_exec(
            *self._command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=self._env,
        )
        self._reader_task = asyncio.create_task(self._read_loop())

    async def disconnect(self) -> None:
        if self._reader_task:
            self._reader_task.cancel()
        if self._proc and self._proc.stdin:
            self._proc.stdin.close()
        if self._proc:
            await self._proc.wait()

    async def initialize(self, name: str = "ya-client", version: str = "0.3.0") -> dict[str, object]:
        return await self._request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": name, "version": version},
        })

    async def list_tools(self) -> list[dict[str, object]]:
        result = await self._request("tools/list", {})
        tools = result.get("tools", [])
        return tools if isinstance(tools, list) else []

    async def call_tool(self, name: str, arguments: dict[str, object]) -> dict[str, object]:
        return await self._request("tools/call", {"name": name, "arguments": arguments})

    async def _request(self, method: str, params: dict[str, object]) -> dict[str, object]:
        request_id = uuid.uuid4().hex[:8]
        future: asyncio.Future[dict[str, object]] = asyncio.get_event_loop().create_future()
        self._pending[request_id] = future

        msg = json.dumps({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params})
        if self._proc and self._proc.stdin:
            self._proc.stdin.write((msg + "\n").encode())
            await self._proc.stdin.drain()

        try:
            return await asyncio.wait_for(future, timeout=30.0)
        except TimeoutError:
            self._pending.pop(request_id, None)
            raise RuntimeError(f"MCP request '{method}' timed out") from None

    async def _read_loop(self) -> None:
        if not self._proc or not self._proc.stdout:
            return
        while True:
            line = await self._proc.stdout.readline()
            if not line:
                break
            try:
                msg = json.loads(line.decode())
                rid = msg.get("id")
                if rid and rid in self._pending:
                    future = self._pending.pop(rid)
                    if "error" in msg:
                        future.set_exception(RuntimeError(str(msg["error"])))
                    else:
                        future.set_result(msg.get("result", {}))
            except json.JSONDecodeError:
                pass
