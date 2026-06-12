from __future__ import annotations

import asyncio
import json
import uuid

from ya.domain.agents.models import AgentEvent, Run, RunStatus
from ya.domain.messages.models import Message, MessageRole, ToolCallRequest
from ya.domain.sessions.models import Session, utc_now
from ya.ports.llm import LLMProvider
from ya.ports.stores import SessionStore
from ya.tools.policy import PermissionPolicy
from ya.tools.registry import registry as tool_registry

SYSTEM_PROMPT = """You are YA, a powerful AI agent running on Linux. You have access to real tools and persistent memory.

## Identity
- You are YA, developed as a personal assistant agent
- You run on a Linux server with file system and shell access
- You have persistent memory that survives across conversations

## Available Tools
{tools}

## Memory System
You have two memory tools:
- `memory_save`: Save facts, preferences, project details to long-term memory
- `memory_search`: Search saved memories BEFORE asking the user

**Critical rule**: ALWAYS search memory (`memory_search`) before asking the user for information they may have shared before. If a user says "remember X", use `memory_save` immediately.

## File System
- `file_read`: Read files or list directories
- `file_write`: Create or modify files

## Shell
- `shell_exec`: Run shell commands (timeout: 30s)
- Use for git, package management, system operations

## Session Management
- `session_search`: List recent sessions
- Help users resume previous conversations

## Task Management
- `task_create`: Create tracked tasks

## Guidelines
- Be concise but thorough
- Use tools proactively — they exist to help
- When reading large files, summarize key points
- Save important user information to memory automatically
- Always search memory before asking for previously-shared information
- Use shell_exec for system operations, file_read/write for file work
"""


class AgentLoopConfig:
    def __init__(self, max_steps: int = 10, run_timeout_seconds: float = 300.0) -> None:
        self.max_steps = max_steps
        self.run_timeout_seconds = run_timeout_seconds


class AgentLoop:
    def __init__(
        self,
        provider: LLMProvider,
        store: SessionStore,
        policy: PermissionPolicy | None = None,
        max_steps: int = 10,
        run_timeout: float = 300.0,
        config: AgentLoopConfig | None = None,
    ) -> None:
        self._provider = provider
        self._store = store
        self._policy = policy or PermissionPolicy()
        if config:
            self._max_steps = config.max_steps
            self._run_timeout = config.run_timeout_seconds
        else:
            self._max_steps = max_steps
            self._run_timeout = run_timeout
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    async def run(self, session: Session, user_input: str) -> Run:
        run = Run(id=_new_id(), session_id=session.id, status=RunStatus.RUNNING)
        await self._store.create_run(run)

        existing = await self._store.get_messages(session.id)
        if not existing:
            tools_desc = self._build_tools_description()
            await self._store.append_message(session.id, Message(
                role=MessageRole.SYSTEM,
                content=SYSTEM_PROMPT.format(tools=tools_desc),
                tool_call_id=_new_id(), created_at=utc_now(),
            ))

        await self._store.append_message(session.id, Message(
            role=MessageRole.USER, content=user_input,
            tool_call_id=_new_id(), created_at=utc_now(),
        ))

        try:
            await self._execute_loop(session, run)
        except Exception:
            if run.status == RunStatus.RUNNING:
                run.status = RunStatus.FAILED
            run.finished_at = utc_now()
            await self._store.update_run(run)
            raise

        if self._cancelled and run.status == RunStatus.RUNNING:
            run.status = RunStatus.CANCELLED
        run.finished_at = run.finished_at or utc_now()
        await self._store.update_run(run)
        return run

    def _build_tools_description(self) -> str:
        lines = []
        for d in tool_registry.list_definitions(enabled_only=True):
            lines.append(f"- **{d.name}** ({d.risk}): {d.description}")
        return "\n".join(lines)

    async def _execute_loop(self, session: Session, run: Run) -> None:
        tools = tool_registry.list_definitions(enabled_only=True)

        for _step in range(self._max_steps):
            if self._cancelled:
                break

            messages = await self._store.get_messages(session.id)
            try:
                response = await asyncio.wait_for(
                    self._provider.generate(messages, tools),
                    timeout=self._run_timeout,
                )
            except TimeoutError:
                run.status = RunStatus.TIMED_OUT
                return

            if response.tool_calls:
                assistant_msg = Message(
                    role=MessageRole.ASSISTANT, content=response.content,
                    tool_calls=response.tool_calls,
                    tool_call_id=_new_id(), created_at=utc_now(),
                )
                await self._store.append_message(session.id, assistant_msg)

                for tc in response.tool_calls:
                    if self._cancelled:
                        break
                    result = await self._execute_tool(tc)
                    await self._store.append_message(session.id, Message(
                        role=MessageRole.TOOL, content=result.content if result.success else f"Error: {result.error}",
                        tool_call_id=tc.id, name=tc.name, created_at=utc_now(),
                    ))
                continue

            if response.content:
                await self._store.append_message(session.id, Message(
                    role=MessageRole.ASSISTANT, content=response.content,
                    tool_call_id=_new_id(), created_at=utc_now(),
                ))
                run.status = RunStatus.COMPLETED
                return

            run.status = RunStatus.COMPLETED
            return

        run.status = RunStatus.TIMED_OUT

    async def _execute_tool(self, tc: ToolCallRequest) -> object:
        entry = tool_registry.get(tc.name)
        if entry is None:
            return type("R", (), {"success": False, "content": "", "error": f"Tool '{tc.name}' not found"})()
        if not entry.definition.enabled:
            return type("R", (), {"success": False, "content": "", "error": f"Tool '{tc.name}' is disabled"})()

        allowed, reason = self._policy.authorize(entry, {})
        if not allowed:
            return type("R", (), {"success": False, "content": "", "error": reason})()

        try:
            args = json.loads(tc.arguments) if isinstance(tc.arguments, str) else tc.arguments
        except json.JSONDecodeError:
            args = {}

        try:
            return await entry.handler.execute(args)
        except Exception as e:
            return type("R", (), {"success": False, "content": "", "error": str(e)})()

    async def _log_event(self, run_id: str, event_type: str, payload: str) -> None:
        await self._store.append_event(run_id, AgentEvent(
            id=_new_id(), run_id=run_id, event_type=event_type,
            payload=payload[:500], created_at=utc_now(),
        ))


def _new_id() -> str:
    return uuid.uuid4().hex[:12]
