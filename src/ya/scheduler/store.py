from __future__ import annotations

import json
from datetime import UTC, datetime

import aiosqlite

from ya.scheduler.models import CronJob, JobRun


class SchedulerStore:
    def __init__(self, db_path: str) -> None:
        self._db_path = db_path

    async def initialize(self) -> None:
        from pathlib import Path
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = await aiosqlite.connect(self._db_path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.execute("PRAGMA journal_mode=WAL")
        await self._conn.execute("PRAGMA foreign_keys=ON")
        await self._migrate()
        await self._conn.commit()

    async def close(self) -> None:
        if self._conn:
            await self._conn.close()

    @property
    def conn(self) -> aiosqlite.Connection:
        if not hasattr(self, "_conn") or self._conn is None:
            raise RuntimeError("Store not initialized")
        return self._conn

    async def _migrate(self) -> None:
        await self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS cron_jobs (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL DEFAULT '',
                job_type TEXT NOT NULL DEFAULT 'prompt',
                payload TEXT NOT NULL DEFAULT '{}',
                schedule_type TEXT NOT NULL DEFAULT 'daily',
                schedule_value TEXT NOT NULL DEFAULT '',
                timezone TEXT NOT NULL DEFAULT 'UTC',
                enabled INTEGER NOT NULL DEFAULT 1,
                job_status TEXT NOT NULL DEFAULT 'active',
                timeout_seconds INTEGER NOT NULL DEFAULT 300,
                retry_policy TEXT NOT NULL DEFAULT '{}',
                max_agent_steps INTEGER NOT NULL DEFAULT 10,
                run_as_role TEXT NOT NULL DEFAULT 'session',
                scope TEXT NOT NULL DEFAULT 'session',
                misfire_policy TEXT NOT NULL DEFAULT 'run_once',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                next_run_at TEXT,
                version INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS job_runs (
                id TEXT PRIMARY KEY,
                job_id TEXT NOT NULL,
                occurrence_key TEXT NOT NULL UNIQUE,
                scheduled_at TEXT NOT NULL,
                started_at TEXT,
                finished_at TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                attempt INTEGER NOT NULL DEFAULT 1,
                trigger TEXT NOT NULL DEFAULT 'scheduled',
                agent_run_id TEXT,
                result_summary TEXT NOT NULL DEFAULT '',
                error_type TEXT NOT NULL DEFAULT '',
                error_message TEXT NOT NULL DEFAULT '',
                log_ref TEXT NOT NULL DEFAULT '',
                FOREIGN KEY (job_id) REFERENCES cron_jobs(id)
            );

            CREATE INDEX IF NOT EXISTS idx_job_runs_job ON job_runs(job_id);
            CREATE INDEX IF NOT EXISTS idx_job_runs_status ON job_runs(status);
        """)

    async def save_job(self, job: CronJob) -> None:
        await self.conn.execute(
            """INSERT OR REPLACE INTO cron_jobs
            (id, name, job_type, payload, schedule_type, schedule_value,
             timezone, enabled, job_status, timeout_seconds, retry_policy,
             max_agent_steps, run_as_role, scope, misfire_policy,
             created_at, updated_at, next_run_at, version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                job.id, job.name, job.job_type.value, json.dumps(job.payload),
                job.schedule_type.value, job.schedule_value, job.timezone,
                int(job.enabled), job.job_status.value, job.timeout_seconds,
                job.retry_policy.model_dump_json(), job.max_agent_steps,
                job.run_as_role, job.scope, job.misfire_policy.value,
                job.created_at, job.updated_at, job.next_run_at, job.version,
            ),
        )
        await self.conn.commit()

    async def get_job(self, job_id: str) -> CronJob | None:
        async with self.conn.execute(
            "SELECT * FROM cron_jobs WHERE id = ?", (job_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return _row_to_job(row) if row else None

    async def list_jobs(self) -> list[CronJob]:
        async with self.conn.execute(
            "SELECT * FROM cron_jobs ORDER BY created_at DESC"
        ) as cursor:
            return [_row_to_job(r) for r in await cursor.fetchall()]

    async def delete_job(self, job_id: str) -> None:
        await self.conn.execute("DELETE FROM cron_jobs WHERE id = ?", (job_id,))
        await self.conn.commit()

    async def update_next_run(self, job_id: str, next_run_at: str | None) -> None:
        await self.conn.execute(
            "UPDATE cron_jobs SET next_run_at = ?, updated_at = ? WHERE id = ?",
            (next_run_at, datetime.now(UTC).isoformat(), job_id),
        )
        await self.conn.commit()

    async def create_run(self, run: JobRun) -> None:
        await self.conn.execute(
            """INSERT INTO job_runs
            (id, job_id, occurrence_key, scheduled_at, started_at,
             finished_at, status, attempt, trigger, agent_run_id,
             result_summary, error_type, error_message, log_ref)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                run.id, run.job_id, run.occurrence_key, run.scheduled_at,
                run.started_at, run.finished_at, run.status.value, run.attempt,
                run.trigger, run.agent_run_id, run.result_summary,
                run.error_type, run.error_message, run.log_ref,
            ),
        )
        await self.conn.commit()

    async def update_run(self, run: JobRun) -> None:
        await self.conn.execute(
            """UPDATE job_runs SET status=?, finished_at=?, attempt=?,
            result_summary=?, error_type=?, error_message=?, log_ref=?
            WHERE id=?""",
            (
                run.status.value, run.finished_at, run.attempt,
                run.result_summary, run.error_type, run.error_message,
                run.log_ref, run.id,
            ),
        )
        await self.conn.commit()

    async def get_runs(self, job_id: str, limit: int = 20) -> list[JobRun]:
        async with self.conn.execute(
            "SELECT * FROM job_runs WHERE job_id = ? ORDER BY scheduled_at DESC LIMIT ?",
            (job_id, limit),
        ) as cursor:
            return [_row_to_run(r) for r in await cursor.fetchall()]

    async def get_due_jobs(self, now: str) -> list[CronJob]:
        async with self.conn.execute(
            """SELECT * FROM cron_jobs
            WHERE enabled = 1 AND job_status = 'active'
            AND next_run_at IS NOT NULL AND next_run_at <= ?""",
            (now,),
        ) as cursor:
            return [_row_to_job(r) for r in await cursor.fetchall()]


def _row_to_job(row: aiosqlite.Row) -> CronJob:
    from ya.scheduler.models import RetryPolicy
    return CronJob(
        id=row["id"],
        name=row["name"],
        job_type=row["job_type"],
        payload=json.loads(row["payload"]),
        schedule_type=row["schedule_type"],
        schedule_value=row["schedule_value"],
        timezone=row["timezone"],
        enabled=bool(row["enabled"]),
        job_status=row["job_status"],
        timeout_seconds=row["timeout_seconds"],
        retry_policy=RetryPolicy.model_validate_json(row["retry_policy"]),
        max_agent_steps=row["max_agent_steps"],
        run_as_role=row["run_as_role"],
        scope=row["scope"],
        misfire_policy=row["misfire_policy"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        next_run_at=row["next_run_at"],
        version=row["version"],
    )


def _row_to_run(row: aiosqlite.Row) -> JobRun:
    return JobRun(
        id=row["id"],
        job_id=row["job_id"],
        occurrence_key=row["occurrence_key"],
        scheduled_at=row["scheduled_at"],
        started_at=row["started_at"],
        finished_at=row["finished_at"],
        status=row["status"],
        attempt=row["attempt"],
        trigger=row["trigger"],
        agent_run_id=row["agent_run_id"],
        result_summary=row["result_summary"],
        error_type=row["error_type"],
        error_message=row["error_message"],
        log_ref=row["log_ref"],
    )
