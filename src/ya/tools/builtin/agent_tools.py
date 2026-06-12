from __future__ import annotations

import asyncio
import os
import platform
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ya.ports.tools import ToolDefinition, ToolResult
from ya.tools.registry import registry


# ── utc_time ──────────────────────────────────────────────────────────
async def _utc_time_handler(self: Any, arguments: dict[str, Any]) -> ToolResult:
    return ToolResult(success=True, content=datetime.now(UTC).isoformat())

registry.register(ToolDefinition(name="utc_time", description="Get current UTC time in ISO 8601 format.", parameters={"type": "object", "properties": {}, "required": []}, source="builtin", risk="safe", enabled=True), handler=type("H", (), {"execute": _utc_time_handler})())


# ── system_info ───────────────────────────────────────────────────────
async def _system_info_handler(self: Any, arguments: dict[str, Any]) -> ToolResult:
    info = f"Time (UTC): {datetime.now(UTC).isoformat()}\nWorking dir: {os.getcwd()}\nOS: {platform.system()} {platform.release()}\nPython: {sys.version.split()[0]}\nHome: {Path.home()}"
    return ToolResult(success=True, content=info)

registry.register(ToolDefinition(name="system_info", description="Get system information: current time, working directory, OS.", parameters={"type": "object", "properties": {}, "required": []}, source="builtin", risk="safe", enabled=True), handler=type("H", (), {"execute": _system_info_handler})())


# ── file_read ─────────────────────────────────────────────────────────
async def _file_read_handler(self: Any, arguments: dict[str, Any]) -> ToolResult:
    path = Path(str(arguments.get("path", ""))).expanduser().resolve()
    offset = int(arguments.get("offset", 0))
    limit = int(arguments.get("limit", 2000))
    if not path.exists():
        return ToolResult(success=False, content="", error=f"File not found: {path}")
    if path.is_dir():
        try:
            entries = sorted(path.iterdir())
            lines = [f"{'[d]' if e.is_dir() else '[f]'} {e.name}" for e in entries[:100]]
            return ToolResult(success=True, content="\n".join(lines))
        except PermissionError:
            return ToolResult(success=False, content="", error=f"Permission denied: {path}")
    try:
        content = path.read_text(encoding="utf-8")
        lines = content.split("\n")
        total = len(lines)
        if limit > 0:
            lines = lines[offset:offset + limit]
        result = "\n".join(lines)
        if len(result) > 8000:
            result = result[:8000] + f"\n... ({total} lines total, truncated)"
        return ToolResult(success=True, content=result or "(empty file)")
    except UnicodeDecodeError:
        return ToolResult(success=False, content="", error=f"Binary file: {path}")
    except PermissionError:
        return ToolResult(success=False, content="", error=f"Permission denied: {path}")

registry.register(ToolDefinition(name="file_read", description="Read file contents or list directory. Use offset/limit for large files.", parameters={"type": "object", "properties": {"path": {"type": "string", "description": "File or directory path"}, "offset": {"type": "integer", "description": "Line offset"}, "limit": {"type": "integer", "description": "Max lines"}}, "required": ["path"]}, source="builtin", risk="safe", enabled=True), handler=type("H", (), {"execute": _file_read_handler})())


# ── file_write ────────────────────────────────────────────────────────
async def _file_write_handler(self: Any, arguments: dict[str, Any]) -> ToolResult:
    path = Path(str(arguments.get("path", ""))).expanduser().resolve()
    content = str(arguments.get("content", ""))
    mode = str(arguments.get("mode", "w"))
    if not content:
        return ToolResult(success=False, content="", error="No content provided")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        if mode == "a":
            with open(path, "a", encoding="utf-8") as f:
                f.write(content)
        else:
            path.write_text(content, encoding="utf-8")
        return ToolResult(success=True, content=f"Written {len(content)} bytes to {path}")
    except PermissionError:
        return ToolResult(success=False, content="", error=f"Permission denied: {path}")
    except Exception as e:
        return ToolResult(success=False, content="", error=str(e))

registry.register(ToolDefinition(name="file_write", description="Write or append content to a file. Creates parent directories.", parameters={"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}, "mode": {"type": "string", "description": "w=overwrite, a=append"}}, "required": ["path", "content"]}, source="builtin", risk="guarded", enabled=True), handler=type("H", (), {"execute": _file_write_handler})())


# ── shell_exec ────────────────────────────────────────────────────────
async def _shell_exec_handler(self: Any, arguments: dict[str, Any]) -> ToolResult:
    cmd = str(arguments.get("command", ""))
    if not cmd:
        return ToolResult(success=False, content="", error="No command")
    try:
        proc = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, cwd=str(Path.home()))
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
        output = stdout.decode(errors="replace")
        if stderr:
            output += "\n[stderr]\n" + stderr.decode(errors="replace")
        return ToolResult(success=proc.returncode == 0, content=output[:4000] or "(no output)")
    except TimeoutError:
        return ToolResult(success=False, content="", error="Timed out after 30s")
    except Exception as e:
        return ToolResult(success=False, content="", error=str(e))

def _shell_available() -> bool:
    return True

registry.register(ToolDefinition(name="shell_exec", description="Execute a shell command. Returns stdout+stderr. Timeout: 30s.", parameters={"type": "object", "properties": {"command": {"type": "string", "description": "Shell command to execute"}}, "required": ["command"]}, source="builtin", risk="dangerous", enabled=True), handler=type("H", (), {"execute": _shell_exec_handler})(), check_fn=_shell_available)


# ── memory_save ───────────────────────────────────────────────────────
_memory_service_ref: Any = None

def set_memory_service(svc: Any) -> None:
    global _memory_service_ref
    _memory_service_ref = svc

async def _memory_save_handler(self: Any, arguments: dict[str, Any]) -> ToolResult:
    title = str(arguments.get("title", ""))
    content = str(arguments.get("content", ""))
    tags = str(arguments.get("tags", ""))
    if not title or not content:
        return ToolResult(success=False, content="", error="title and content required")
    if _memory_service_ref:
        try:
            mid = await _memory_service_ref.add(title, content, tags=tags)
            return ToolResult(success=True, content=f"Saved: {mid}")
        except Exception as e:
            return ToolResult(success=False, content="", error=str(e))
    return ToolResult(success=False, content="", error="Memory service not available")

registry.register(ToolDefinition(name="memory_save", description="Save information to persistent memory. Use for user facts, preferences, project context.", parameters={"type": "object", "properties": {"title": {"type": "string"}, "content": {"type": "string"}, "tags": {"type": "string", "description": "Comma-separated tags"}}, "required": ["title", "content"]}, source="builtin", risk="safe", enabled=True), handler=type("H", (), {"execute": _memory_save_handler})())


# ── memory_search ─────────────────────────────────────────────────────
async def _memory_search_handler(self: Any, arguments: dict[str, Any]) -> ToolResult:
    query = str(arguments.get("query", ""))
    if not query:
        return ToolResult(success=False, content="", error="Query required")
    if _memory_service_ref:
        try:
            results = await _memory_service_ref.search(query=query, limit=5)
            if not results:
                return ToolResult(success=True, content="No matching memories found.")
            lines = [f"- [{r['id']}] {r['title']}: {r['content'][:200]}" for r in results]
            return ToolResult(success=True, content="\n".join(lines))
        except Exception as e:
            return ToolResult(success=False, content="", error=str(e))
    return ToolResult(success=False, content="", error="Memory service not available")

registry.register(ToolDefinition(name="memory_search", description="Search saved memories. Use BEFORE asking user for information they may have shared before.", parameters={"type": "object", "properties": {"query": {"type": "string", "description": "Search keywords"}}, "required": ["query"]}, source="builtin", risk="safe", enabled=True), handler=type("H", (), {"execute": _memory_search_handler})())


# ── memory_get ─────────────────────────────────────────────────────────
async def _memory_get_handler(self: Any, arguments: dict[str, Any]) -> ToolResult:
    memory_id = str(arguments.get("memory_id", ""))
    if not memory_id:
        return ToolResult(success=False, content="", error="memory_id required")
    if _memory_service_ref:
        try:
            mem = await _memory_service_ref.show(memory_id)
            if mem:
                return ToolResult(success=True, content=f"Title: {mem['title']}\nContent: {mem['content']}\nTags: {mem['tags']}")
            return ToolResult(success=True, content=f"Memory '{memory_id}' not found.")
        except Exception as e:
            return ToolResult(success=False, content="", error=str(e))
    return ToolResult(success=False, content="", error="Memory service not available")

registry.register(ToolDefinition(name="memory_get", description="Retrieve a specific memory by its ID. Use when user references a memory ID directly.", parameters={"type": "object", "properties": {"memory_id": {"type": "string", "description": "Memory ID (e.g. mem-c2e89d83)"}}, "required": ["memory_id"]}, source="builtin", risk="safe", enabled=True), handler=type("H", (), {"execute": _memory_get_handler})())


# ── session_search ────────────────────────────────────────────────────
_session_store_ref: Any = None

def set_session_store(store: Any) -> None:
    global _session_store_ref
    _session_store_ref = store

async def _session_search_handler(self: Any, arguments: dict[str, Any]) -> ToolResult:
    if _session_store_ref:
        try:
            sessions = await _session_store_ref.list_sessions()
            lines = [f"[{s.status.value}] {s.id[:8]} — {s.title[:50]}" for s in sessions[:20]]
            return ToolResult(success=True, content="\n".join(lines) if lines else "No sessions.")
        except Exception as e:
            return ToolResult(success=False, content="", error=str(e))
    return ToolResult(success=False, content="", error="Session store not available")

registry.register(ToolDefinition(name="session_search", description="List recent sessions. Use to help user resume previous conversations.", parameters={"type": "object", "properties": {}, "required": []}, source="builtin", risk="safe", enabled=True), handler=type("H", (), {"execute": _session_search_handler})())


# ── task_create ───────────────────────────────────────────────────────
async def _task_create_handler(self: Any, arguments: dict[str, Any]) -> ToolResult:
    title = str(arguments.get("title", ""))
    description = str(arguments.get("description", ""))
    if not title:
        return ToolResult(success=False, content="", error="Title required")
    tid = f"task-{uuid.uuid4().hex[:8]}"
    return ToolResult(success=True, content=f"Task created: {tid} — {title}\n{description}")

registry.register(ToolDefinition(name="task_create", description="Create a task for tracking work. Use for TODO items, feature requests, bug reports.", parameters={"type": "object", "properties": {"title": {"type": "string"}, "description": {"type": "string"}}, "required": ["title"]}, source="builtin", risk="safe", enabled=True), handler=type("H", (), {"execute": _task_create_handler})())
