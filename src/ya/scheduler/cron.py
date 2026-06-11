from __future__ import annotations

from datetime import UTC, datetime, timedelta

from croniter import croniter

from ya.scheduler.models import (
    CronJob,
    MisfirePolicy,
    ScheduleType,
)


def calculate_next_run(job: CronJob, after: datetime | None = None) -> datetime | None:
    if not job.enabled or job.job_status.value != "active":
        return None

    base = after or datetime.now(UTC)

    if job.schedule_type == ScheduleType.CRON:
        try:
            cron = croniter(job.schedule_value, base)
            result = cron.get_next(datetime)
            return result if isinstance(result, datetime) else None
        except (ValueError, KeyError):
            return None

    if job.schedule_type == ScheduleType.INTERVAL:
        seconds = _parse_interval_seconds(job.schedule_value)
        if seconds is None:
            return None
        return base + timedelta(seconds=seconds)

    if job.schedule_type == ScheduleType.DAILY:
        hour, minute = _parse_time(job.schedule_value, 9, 0)
        next_run = base.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if next_run <= base:
            next_run += timedelta(days=1)
        return next_run

    if job.schedule_type == ScheduleType.WEEKLY:
        day, hour, minute = _parse_weekly(job.schedule_value)
        next_run = base.replace(hour=hour, minute=minute, second=0, microsecond=0)
        days_ahead = day - next_run.weekday()
        if days_ahead < 0 or (days_ahead == 0 and next_run <= base):
            days_ahead += 7
        return next_run + timedelta(days=days_ahead)

    if job.schedule_type == ScheduleType.MONTHLY:
        day, hour, minute = _parse_monthly(job.schedule_value)
        try:
            next_run = base.replace(day=min(day, 28), hour=hour, minute=minute, second=0, microsecond=0)
        except ValueError:
            return None
        if next_run <= base:
            if base.month == 12:
                next_run = next_run.replace(year=base.year + 1, month=1)
            else:
                next_run = next_run.replace(month=base.month + 1)
        return next_run

    return None


def get_misfire_occurrence(
    job: CronJob,
    last_run_at: datetime | None,
    now: datetime,
) -> datetime | None:
    if last_run_at is None:
        return calculate_next_run(job, after=now)
    if job.misfire_policy == MisfirePolicy.SKIP:
        return calculate_next_run(job, after=now)
    next = calculate_next_run(job, after=last_run_at)
    if next and next <= now:
        return next
    return calculate_next_run(job, after=now)


def _parse_interval_seconds(value: str) -> int | None:
    try:
        return int(value)
    except ValueError:
        return None


def _parse_time(value: str, default_hour: int = 9, default_minute: int = 0) -> tuple[int, int]:
    try:
        parts = value.split(":")
        return int(parts[0]), int(parts[1]) if len(parts) > 1 else default_minute
    except (ValueError, IndexError):
        return default_hour, default_minute


def _parse_weekly(value: str) -> tuple[int, int, int]:
    days = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}
    try:
        parts = value.split(":")
        day = days.get(parts[0].lower(), 0)
        hour = int(parts[1]) if len(parts) > 1 else 9
        minute = int(parts[2]) if len(parts) > 2 else 0
        return day, hour, minute
    except (ValueError, IndexError):
        return 0, 9, 0


def _parse_monthly(value: str) -> tuple[int, int, int]:
    try:
        parts = value.split(":")
        day = int(parts[0])
        hour = int(parts[1]) if len(parts) > 1 else 9
        minute = int(parts[2]) if len(parts) > 2 else 0
        return day, hour, minute
    except (ValueError, IndexError):
        return 1, 9, 0
