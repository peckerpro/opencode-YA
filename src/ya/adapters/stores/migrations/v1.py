from __future__ import annotations

import aiosqlite

SCHEMA_VERSION = 1


async def apply_migrations(conn: aiosqlite.Connection) -> None:
    await conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_version (version INTEGER PRIMARY KEY)"
    )
    async with conn.execute("SELECT MAX(version) FROM schema_version") as cursor:
        row = await cursor.fetchone()
        current = row[0] if row and row[0] is not None else 0

    if current < 1:
        await _migrate_v1(conn)


async def _migrate_v1(conn: aiosqlite.Connection) -> None:
    await conn.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'active',
            default_agent_id TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            last_activity_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT,
            tool_calls TEXT,
            tool_call_id TEXT,
            name TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        );

        CREATE TABLE IF NOT EXISTS runs (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            agent_id TEXT NOT NULL DEFAULT '',
            role_id TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'pending',
            started_at TEXT NOT NULL,
            finished_at TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        );

        CREATE TABLE IF NOT EXISTS agent_events (
            id TEXT PRIMARY KEY,
            run_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            payload TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            FOREIGN KEY (run_id) REFERENCES runs(id)
        );

        CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);
        CREATE INDEX IF NOT EXISTS idx_runs_session ON runs(session_id);
        CREATE INDEX IF NOT EXISTS idx_events_run ON agent_events(run_id);
    """)
    await conn.execute("INSERT INTO schema_version (version) VALUES (1)")
