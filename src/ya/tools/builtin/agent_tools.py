from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ya.application.memory_service import MemoryService
from ya.ports.tools import ToolDefinition, ToolResult


class FileReadTool:
    definition = ToolDefinition(
        name="file_read",
        description="Read the contents of a file. Returns the file content as text.",
        parameters={"type": "object", "properties": {"path": {"type": "string", "description": "Path to the file to read"}}, "required": ["path"]},
        source="builtin", risk="safe", enabled=True,
    )

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        path = Path(str(arguments.get("path", "")))
        if not path.exists():
            return ToolResult(success=False, content="", error=f"File not found: {path}")
        try:
            content = path.read_text(encoding="utf-8")
            if len(content) > 8000:
                content = content[:8000] + f"\n... (truncated, {len(content)} total bytes)"
            return ToolResult(success=True, content=content)
        except Exception as e:
            return ToolResult(success=False, content="", error=str(e))


class FileWriteTool:
    definition = ToolDefinition(
        name="file_write",
        description="Write content to a file. Creates the file if it doesn't exist, overwrites if it does.",
        parameters={"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]},
        source="builtin", risk="guarded", enabled=True,
    )

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        path = Path(str(arguments.get("path", "")))
        content = str(arguments.get("content", ""))
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            return ToolResult(success=True, content=f"Written {len(content)} bytes to {path}")
        except Exception as e:
            return ToolResult(success=False, content="", error=str(e))


class ShellExecTool:
    definition = ToolDefinition(
        name="shell_exec",
        description="Execute a shell command and return stdout. Use for system operations.",
        parameters={"type": "object", "properties": {"command": {"type": "string", "description": "Shell command to execute"}}, "required": ["command"]},
        source="builtin", risk="dangerous", enabled=True,
    )

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        import asyncio
        cmd = str(arguments.get("command", ""))
        if not cmd:
            return ToolResult(success=False, content="", error="No command provided")
        try:
            proc = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
            output = stdout.decode(errors="replace")
            if stderr:
                output += "\n[stderr]\n" + stderr.decode(errors="replace")
            return ToolResult(success=proc.returncode == 0, content=output[:4000] or "(no output)")
        except TimeoutError:
            return ToolResult(success=False, content="", error="Command timed out after 30s")
        except Exception as e:
            return ToolResult(success=False, content="", error=str(e))


class SystemInfoTool:
    definition = ToolDefinition(
        name="system_info",
        description="Get system information: current time, working directory, OS details.",
        parameters={"type": "object", "properties": {}, "required": []},
        source="builtin", risk="safe", enabled=True,
    )

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        import os
        import platform
        import sys
        info = f"Time (UTC): {datetime.now(UTC).isoformat()}\n"
        info += f"Working dir: {os.getcwd()}\n"
        info += f"OS: {platform.system()} {platform.release()}\n"
        info += f"Python: {sys.version.split()[0]}\n"
        info += f"Home: {Path.home()}"
        return ToolResult(success=True, content=info)


class MemorySaveTool:
    def __init__(self, memory_service: MemoryService) -> None:
        self._memory = memory_service
        self.definition = ToolDefinition(
            name="memory_save",
            description="Save information to long-term memory. Use this to remember facts, preferences, or important context.",
            parameters={"type": "object", "properties": {"title": {"type": "string"}, "content": {"type": "string"}, "tags": {"type": "string", "description": "Comma-separated tags"}}, "required": ["title", "content"]},
            source="builtin", risk="safe", enabled=True,
        )

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        title = str(arguments.get("title", ""))
        content = str(arguments.get("content", ""))
        tags = str(arguments.get("tags", ""))
        if not title or not content:
            return ToolResult(success=False, content="", error="title and content required")
        try:
            mid = await self._memory.add(title, content, tags=tags)
            return ToolResult(success=True, content=f"Memory saved: {mid} — {title}")
        except Exception as e:
            return ToolResult(success=False, content="", error=str(e))


class MemorySearchTool:
    def __init__(self, memory_service: MemoryService) -> None:
        self._memory = memory_service
        self.definition = ToolDefinition(
            name="memory_search",
            description="Search your long-term memory for saved information. Use this to recall facts, preferences, or past context.",
            parameters={"type": "object", "properties": {"query": {"type": "string", "description": "Search query"}}, "required": ["query"]},
            source="builtin", risk="safe", enabled=True,
        )

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        query = str(arguments.get("query", ""))
        if not query:
            return ToolResult(success=False, content="", error="query required")
        try:
            results = await self._memory.search(query=query, limit=10)
            if not results:
                return ToolResult(success=True, content="No memories found matching your query.")
            lines = [f"- [{r['id']}] {r['title']}: {r['content'][:200]}" for r in results]
            return ToolResult(success=True, content="\n".join(lines))
        except Exception as e:
            return ToolResult(success=False, content="", error=str(e))
