import asyncio
import logging

_shutdown_event: asyncio.Event | None = None
_shutdown_reason: str | None = None


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
