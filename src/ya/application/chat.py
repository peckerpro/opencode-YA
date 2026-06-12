from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

from ya.domain.agents.models import AgentEvent, Run, RunStatus
from ya.domain.messages.models import (
    LLMStreamEvent,
    Message,
    MessageRole,
    ToolCallRequest,
)
from ya.domain.sessions.models import Session, utc_now
from ya.permissions.audit import AuditEvent, AuditStore
from ya.ports.llm import LLMProvider
from ya.ports.stores import SessionStore
from ya.tools.policy import PermissionPolicy
from ya.tools.registry import ToolRegistry


class AgentLoopConfig:
    def __init__(
        self,
        max_steps: int = 10,
        run_timeout_seconds: float = 300.0,
    ) -> None:
        self.max_steps = max_steps
        self.run_timeout_seconds = run_timeout_seconds


class AgentLoop:
    def __init__(
        self,
        provider: LLMProvider,
        store: SessionStore,
        registry: ToolRegistry,
        policy: PermissionPolicy,
        config: AgentLoopConfig | None = None,
        audit_store: AuditStore | None = None,
    ) -> None:
        self._provider = provider
        self._store = store
        self._registry = registry
        self._policy = policy
        self._config = config or AgentLoopConfig()
        self._cancelled = False
        self._audit = audit_store or AuditStore()

    def cancel(self) -> None:
        self._cancelled = True

    async def run(
        self,
        session: Session,
        user_input: str,
        agent_id: str = "",
        role_id: str = "",
    ) -> Run:
        run = Run(
            id=_new_id(),
            session_id=session.id,
            agent_id=agent_id,
            role_id=role_id,
            status=RunStatus.RUNNING,
        )
        await self._store.create_run(run)

        user_msg = Message(
            role=MessageRole.USER,
            content=user_input,
            tool_call_id=_new_id(),
            created_at=utc_now(),
        )
        await self._store.append_message(session.id, user_msg)

        try:
            await self._execute_loop(session, run)
        except Exception:
            run.status = RunStatus.FAILED
            run.finished_at = utc_now()
            await self._store.update_run(run)
            raise

        if self._cancelled:
            run.status = RunStatus.CANCELLED
        run.finished_at = utc_now()
        await self._store.update_run(run)
        return run

    async def run_stream(
        self,
        session: Session,
        user_input: str,
        agent_id: str = "",
        role_id: str = "",
    ) -> AsyncGenerator[LLMStreamEvent | Run, None]:
        run = Run(
            id=_new_id(),
            session_id=session.id,
            agent_id=agent_id,
            role_id=role_id,
            status=RunStatus.RUNNING,
        )
        await self._store.create_run(run)

        user_msg = Message(
            role=MessageRole.USER,
            content=user_input,
            tool_call_id=_new_id(),
            created_at=utc_now(),
        )
        await self._store.append_message(session.id, user_msg)

        tools = self._registry.list_definitions(enabled_only=True)
        try:
            stream = await self._provider.generate_stream(
                await self._store.get_messages(session.id),
                tools,
            )
            async for event in stream:
                yield event
                if event.event_type == "finish":
                    break

            run.status = RunStatus.COMPLETED
        except Exception:
            run.status = RunStatus.FAILED

        run.finished_at = utc_now()
        await self._store.update_run(run)
        yield run

    async def _execute_loop(self, session: Session, run: Run) -> None:
        tools = self._registry.list_definitions(enabled_only=True)

        for _step in range(self._config.max_steps):
            if self._cancelled:
                break

            messages = await self._store.get_messages(session.id)
            response = await self._provider.generate(messages, tools)

            if response.tool_calls:
                assistant_msg = Message(
                    role=MessageRole.ASSISTANT,
                    content=response.content,
                    tool_calls=response.tool_calls,
                    tool_call_id=_new_id(),
                    created_at=utc_now(),
                )
                await self._store.append_message(session.id, assistant_msg)
                await self._log_event(run.id, "tool_call", str(response.tool_calls))

                for tc in response.tool_calls:
                    if self._cancelled:
                        break

                    tool = self._registry.get(tc.name)
                    if tool is None:
                        await self._handle_missing_tool(session, tc)
                        continue

                    allowed, reason = self._policy.authorize(tool, {})
                    if not allowed:
                        await self._handle_denied_tool(session, tc, reason)
                        continue

                    try:
                        import json
                        arguments = json.loads(tc.arguments)
                    except json.JSONDecodeError:
                        await self._handle_invalid_args(session, tc)
                        continue

                    result = await self._registry.execute(tc.name, arguments)
                    self._audit.append(AuditEvent(
                        capability=f"tool.execute.{tool.definition.risk}",
                        actor_agent_id=run.agent_id,
                        target_type="tool",
                        target_id=tc.name,
                        decision="allowed",
                        result_status="success" if result.success else "error",
                    ))
                    tool_msg = Message(
                        role=MessageRole.TOOL,
                        content=result.content if result.success else f"Error: {result.error}",
                        tool_call_id=tc.id,
                        name=tc.name,
                        created_at=utc_now(),
                    )
                    await self._store.append_message(session.id, tool_msg)
                    await self._log_event(run.id, "tool_result", result.content)

                continue

            if response.content:
                assistant_msg = Message(
                    role=MessageRole.ASSISTANT,
                    content=response.content,
                    tool_call_id=_new_id(),
                    created_at=utc_now(),
                )
                await self._store.append_message(session.id, assistant_msg)
                await self._log_event(run.id, "text_response", response.content)
                run.status = RunStatus.COMPLETED
                break

            run.status = RunStatus.COMPLETED
            break
        else:
            run.status = RunStatus.TIMED_OUT

    async def _handle_missing_tool(
        self, session: Session, tc: ToolCallRequest
    ) -> Message:
        msg = Message(
            role=MessageRole.TOOL,
            content=f"Error: Tool '{tc.name}' not found",
            tool_call_id=tc.id,
            name=tc.name,
            created_at=utc_now(),
        )
        await self._store.append_message(session.id, msg)
        return msg

    async def _handle_denied_tool(
        self, session: Session, tc: ToolCallRequest, reason: str
    ) -> Message:
        msg = Message(
            role=MessageRole.TOOL,
            content=f"Error: {reason}",
            tool_call_id=tc.id,
            name=tc.name,
            created_at=utc_now(),
        )
        await self._store.append_message(session.id, msg)
        return msg

    async def _handle_invalid_args(
        self, session: Session, tc: ToolCallRequest
    ) -> None:
        msg = Message(
            role=MessageRole.TOOL,
            content=f"Error: Invalid arguments for tool '{tc.name}'",
            tool_call_id=tc.id,
            name=tc.name,
            created_at=utc_now(),
        )
        await self._store.append_message(session.id, msg)

    async def _log_event(self, run_id: str, event_type: str, payload: str) -> None:
        event = AgentEvent(
            id=_new_id(),
            run_id=run_id,
            event_type=event_type,
            payload=payload[:500],
            created_at=utc_now(),
        )
        await self._store.append_event(run_id, event)


def _new_id() -> str:
    return uuid.uuid4().hex[:12]
