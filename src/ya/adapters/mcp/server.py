from __future__ import annotations

import asyncio
import json
import sys
from typing import Any

from ya.tools.registry import ToolRegistry


class MCPServer:
    def __init__(self, registry: ToolRegistry, name: str = "ya-mcp", version: str = "0.3.0") -> None:
        self._registry = registry
        self._name = name
        self._version = version
        self._initialized = False

    async def run(self) -> None:
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin)

        w_transport, w_protocol = await asyncio.get_event_loop().connect_write_pipe(
            asyncio.streams.FlowControlMixin, sys.stdout
        )
        writer = asyncio.StreamWriter(w_transport, w_protocol, reader, asyncio.get_event_loop())

        while True:
            line = await reader.readline()
            if not line:
                break
            try:
                request = json.loads(line.decode())
                response = await self._handle_request(request)
                writer.write((json.dumps(response) + "\n").encode())
                await writer.drain()
            except json.JSONDecodeError:
                pass

    async def _handle_request(self, request: dict[str, Any]) -> dict[str, Any]:
        rid = request.get("id")
        method = request.get("method", "")
        params = request.get("params", {})

        try:
            if method == "initialize":
                result = await self._handle_initialize(params)
            elif method == "tools/list":
                result = await self._handle_tools_list()
            elif method == "tools/call":
                result = await self._handle_tools_call(params)
            elif method == "notifications/initialized":
                return {}
            else:
                return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": f"Method not found: {method}"}}

            return {"jsonrpc": "2.0", "id": rid, "result": result}
        except Exception as e:
            return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32000, "message": str(e)}}

    async def _handle_initialize(self, params: dict[str, Any]) -> dict[str, Any]:
        self._initialized = True
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": self._name, "version": self._version},
        }

    async def _handle_tools_list(self) -> dict[str, Any]:
        tools = []
        for d in self._registry.list_definitions(enabled_only=True):
            tools.append({
                "name": d.name,
                "description": d.description,
                "inputSchema": d.parameters,
            })
        return {"tools": tools}

    async def _handle_tools_call(self, params: dict[str, Any]) -> dict[str, Any]:
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})
        result = await self._registry.execute(tool_name, arguments)
        return {
            "content": [{"type": "text", "text": result.content if result.success else f"Error: {result.error}"}],
            "isError": not result.success,
        }
