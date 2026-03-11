import asyncio
import math
import logging
from datetime import datetime, timedelta, timezone

_shutdown_event: asyncio.Event | None = None
_shutdown_reason: str | None = None
_last_restart_time: datetime | None = None
_worker_timezone = timezone(timedelta(hours=3))


def set_shutdown_event(event: asyncio.Event) -> None:
    global _shutdown_event
    _shutdown_event = event


def request_shutdown(reason: str) -> None:
    global _shutdown_reason
    _shutdown_reason = reason
    if _shutdown_event is None:
        logging.error("Shutdown requested but shutdown event is not initialized: %s", reason)
        return
    _shutdown_event.set()


def get_shutdown_reason() -> str | None:
    return _shutdown_reason


def get_worker_now() -> datetime:
    return datetime.now(_worker_timezone)


def set_last_restart_time(restarted_at: datetime | None = None) -> datetime:
    global _last_restart_time
    _last_restart_time = restarted_at or get_worker_now()
    return _last_restart_time


def get_minutes_until_next_restart(reset_after_mins: int, *, now: datetime | None = None) -> int | None:
    if reset_after_mins <= 0:
        return 0
    if _last_restart_time is None:
        return reset_after_mins

    current_time = now or get_worker_now()
    remaining_seconds = (_last_restart_time + timedelta(minutes=reset_after_mins) - current_time).total_seconds()
    if remaining_seconds <= 0:
        return 0
    return math.ceil(remaining_seconds / 60)
