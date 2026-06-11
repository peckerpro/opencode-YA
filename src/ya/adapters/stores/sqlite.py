from __future__ import annotations

import json
import uuid
from pathlib import Path

import aiosqlite

from ya.adapters.stores.migrations import apply_migrations
from ya.domain.agents.models import AgentEvent, Run, RunStatus
from ya.domain.messages.models import Message, MessageRole, ToolCallRequest
from ya.domain.sessions.models import Session, SessionStatus


class SqliteSessionStore:
    def __init__(self, db_path: str | Path) -> None:
        self._db_path = str(db_path)
        self._conn: aiosqlite.Connection | None = None

    async def initialize(self) -> None:
        parent = Path(self._db_path).parent
        parent.mkdir(parents=True, exist_ok=True)
        self._conn = await aiosqlite.connect(self._db_path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.execute("PRAGMA journal_mode=WAL")
        await self._conn.execute("PRAGMA foreign_keys=ON")
        await apply_migrations(self._conn)
        await self._conn.commit()

    async def close(self) -> None:
        if self._conn:
            await self._conn.close()
            self._conn = None

    @property
    def conn(self) -> aiosqlite.Connection:
        if self._conn is None:
            raise RuntimeError("Store not initialized — call initialize() first")
        return self._conn

    async def create_session(self, session: Session) -> None:
        await self.conn.execute(
            "INSERT INTO sessions (id, title, status, default_agent_id, created_at, updated_at, last_activity_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                session.id,
                session.title,
                session.status.value,
                session.default_agent_id,
                session.created_at,
                session.updated_at,
                session.last_activity_at,
            ),
        )
        await self.conn.commit()

    async def get_session(self, session_id: str) -> Session | None:
        async with self.conn.execute(
            "SELECT * FROM sessions WHERE id = ?", (session_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row is None:
                return None
            return _row_to_session(row)

    async def list_sessions(self) -> list[Session]:
        async with self.conn.execute(
            "SELECT * FROM sessions ORDER BY last_activity_at DESC"
        ) as cursor:
            rows = await cursor.fetchall()
            return [_row_to_session(r) for r in rows]

    async def update_session(self, session: Session) -> None:
        await self.conn.execute(
            "UPDATE sessions SET title=?, status=?, default_agent_id=?, "
            "updated_at=?, last_activity_at=? WHERE id=?",
            (
                session.title,
                session.status.value,
                session.default_agent_id,
                session.updated_at,
                session.last_activity_at,
                session.id,
            ),
        )
        await self.conn.commit()

    async def append_message(self, session_id: str, message: Message) -> None:
        await self.conn.execute(
            "INSERT INTO messages (id, session_id, role, content, tool_calls, "
            "tool_call_id, name, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                message.tool_call_id or _new_id(),
                session_id,
                message.role.value,
                message.content,
                message.tool_calls and _serialize_tool_calls(message.tool_calls),
                message.tool_call_id,
                message.name,
                message.created_at,
            ),
        )
        await self.conn.execute(
            "UPDATE sessions SET last_activity_at = ? WHERE id = ?",
            (message.created_at, session_id),
        )
        await self.conn.commit()

    async def get_messages(self, session_id: str) -> list[Message]:
        async with self.conn.execute(
            "SELECT * FROM messages WHERE session_id = ? ORDER BY rowid ASC",
            (session_id,),
        ) as cursor:
            rows = await cursor.fetchall()
            return [_row_to_message(r) for r in rows]

    async def create_run(self, run: Run) -> None:
        await self.conn.execute(
            "INSERT INTO runs (id, session_id, agent_id, role_id, status, "
            "started_at, finished_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                run.id,
                run.session_id,
                run.agent_id,
                run.role_id,
                run.status.value,
                run.started_at,
                run.finished_at,
            ),
        )
        await self.conn.commit()

    async def update_run(self, run: Run) -> None:
        await self.conn.execute(
            "UPDATE runs SET status=?, finished_at=? WHERE id=?",
            (run.status.value, run.finished_at, run.id),
        )
        await self.conn.commit()

    async def get_run(self, run_id: str) -> Run | None:
        async with self.conn.execute(
            "SELECT * FROM runs WHERE id = ?", (run_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row is None:
                return None
            return _row_to_run(row)

    async def append_event(self, run_id: str, event: AgentEvent) -> None:
        await self.conn.execute(
            "INSERT INTO agent_events (id, run_id, event_type, payload, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (event.id, run_id, event.event_type, event.payload, event.created_at),
        )
        await self.conn.commit()


def _row_to_session(row: aiosqlite.Row) -> Session:
    return Session(
        id=row["id"],
        title=row["title"],
        status=SessionStatus(row["status"]),
        default_agent_id=row["default_agent_id"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        last_activity_at=row["last_activity_at"],
    )


def _row_to_message(row: aiosqlite.Row) -> Message:
    tool_calls = None
    if row["tool_calls"]:
        tc_data = json.loads(row["tool_calls"])
        tool_calls = [ToolCallRequest(**tc) for tc in tc_data]
    return Message(
        role=MessageRole(row["role"]),
        content=row["content"],
        tool_calls=tool_calls,
        tool_call_id=row["tool_call_id"],
        name=row["name"],
        created_at=row["created_at"],
    )


def _row_to_run(row: aiosqlite.Row) -> Run:
    return Run(
        id=row["id"],
        session_id=row["session_id"],
        agent_id=row["agent_id"],
        role_id=row["role_id"],
        status=RunStatus(row["status"]),
        started_at=row["started_at"],
        finished_at=row["finished_at"],
    )
def _new_id() -> str:
    return uuid.uuid4().hex[:12]


def _serialize_tool_calls(tool_calls: list[ToolCallRequest]) -> str:
    return json.dumps([tc.model_dump() for tc in tool_calls])
