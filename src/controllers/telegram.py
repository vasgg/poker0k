import asyncio
import logging
from io import BytesIO
import json
from pathlib import Path

import aiofiles
from aiohttp import ClientError, ClientSession, ClientTimeout, FormData, TCPConnector
import socket

from internal.consts import WorkspaceCoords
from internal.schemas import Task


def _trim_text(text: str | None, limit: int = 500) -> str:
    if not text:
        return ""
    return text if len(text) <= limit else f"{text[:limit]}..."


def _format_exc(exc: BaseException) -> str:
    return _trim_text(f"{type(exc).__name__}: {exc}")


def _parse_retry_after(body: str) -> float | None:
    try:
        payload = json.loads(body)
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    params = payload.get("parameters")
    if not isinstance(params, dict):
        return None
    retry_after = params.get("retry_after")
    if isinstance(retry_after, (int, float)) and retry_after > 0:
        return float(retry_after)
    return None


def _extract_description(body: str) -> str | None:
    try:
        payload = json.loads(body)
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    description = payload.get("description")
    if isinstance(description, str) and description.strip():
        return description.strip()
    return None


class TelegramAPIResponseError(RuntimeError):
    def __init__(self, *, method: str, status: int, body: str):
        self.method = method
        self.status = status
        self.body = body
        description = _extract_description(body) or body
        super().__init__(f"Telegram API {method} failed with HTTP {status}: {_trim_text(description)}")


class TelegramDeliveryError(RuntimeError):
    def __init__(self, chat_id: int, original_exc: BaseException, task: Task | None = None):
        super().__init__(f"Telegram reporting failed for chat {chat_id}: {_format_exc(original_exc)}")
        self.chat_id = chat_id
        self.original_exc = original_exc
        self.task = task


async def send_telegram_report(
    message: str,
    chats: tuple,
    task: Task | None = None,
    image: Path | BytesIO | bytes | None = None,
    disable_notification: bool = False,
    retries: int = 3,
    retry_delays: tuple[float, ...] = (2.0, 5.0, 10.0),
    raise_on_fail: bool = True,
    *,
    session: ClientSession | None = None,
) -> None:
    from config import settings

    text = f"{task.order_id}|{task.requisite}|${task.amount}|{message}" if task else message
    token = settings.TG_BOT_TOKEN.get_secret_value()

    timeout = ClientTimeout(total=10)
    owns_session = session is None
    if owns_session:
        session = ClientSession(timeout=timeout, connector=TCPConnector(family=socket.AF_INET))

    retries = max(1, retries)
    try:
        chat_ids = tuple(chats)
        if not chat_ids:
            return
        method = "sendPhoto" if image is not None else "sendMessage"
        url = f"https://api.telegram.org/bot{token}/{method}"
        try:
            if image is not None:
                if isinstance(image, Path):
                    async with aiofiles.open(image, "rb") as f:
                        img_bytes = await f.read()
                    filename = image.name
                elif isinstance(image, BytesIO):
                    img_bytes = image.getvalue()
                    filename = "screenshot.png"
                elif isinstance(image, (bytes, bytearray)):
                    img_bytes = bytes(image)
                    filename = "screenshot.png"
                else:
                    raise ValueError("Unsupported image type")
            else:
                img_bytes = None
                filename = None
        except Exception as exc:
            logging.error(
                "Failed to prepare telegram payload (%s) for %s chat(s): %s",
                method,
                len(chat_ids),
                _format_exc(exc),
            )
            if raise_on_fail and chat_ids:
                raise TelegramDeliveryError(chat_id=chat_ids[0], original_exc=exc, task=task) from exc
            return

        for chat_id in chat_ids:

            for attempt in range(1, retries + 1):
                try:
                    if image is not None:
                        data = FormData()
                        data.add_field("chat_id", str(chat_id))
                        data.add_field("caption", text)
                        data.add_field("disable_notification", str(disable_notification).lower())
                        data.add_field("photo", img_bytes, filename=filename, content_type="image/png")  # type: ignore[arg-type]
                    else:
                        data = {
                            "chat_id": str(chat_id),
                            "text": text,
                            "disable_notification": str(disable_notification).lower(),
                        }
                    async with session.post(url, data=data, ssl=False, timeout=timeout) as resp:
                        body = await resp.text()
                        if resp.status >= 400:
                            api_exc = TelegramAPIResponseError(method=method, status=resp.status, body=body)
                            retriable = resp.status == 429 or resp.status >= 500
                            if not retriable or attempt >= retries:
                                logging.error(
                                    "Telegram API error for chat %s (%s) after %s/%s attempts: %s",
                                    chat_id,
                                    method,
                                    attempt,
                                    retries,
                                    _format_exc(api_exc),
                                )
                                if raise_on_fail:
                                    raise TelegramDeliveryError(
                                        chat_id=chat_id,
                                        original_exc=api_exc,
                                        task=task,
                                    ) from api_exc
                                break

                            retry_after = _parse_retry_after(body)
                            delay_idx = max(0, attempt - 1)
                            delay = retry_after or retry_delays[min(delay_idx, len(retry_delays) - 1)]
                            logging.warning(
                                "Telegram API error for chat %s (%s) (attempt %s/%s), retrying in %ss: %s",
                                chat_id,
                                method,
                                attempt,
                                retries,
                                delay,
                                _format_exc(api_exc),
                            )
                            await asyncio.sleep(delay)
                            continue
                    break
                except (ClientError, asyncio.TimeoutError) as exc:
                    if attempt >= retries:
                        logging.error(
                            "Failed to send telegram report to chat %s (%s) after %s attempts: %s",
                            chat_id,
                            method,
                            retries,
                            _format_exc(exc),
                        )
                        if raise_on_fail:
                            raise TelegramDeliveryError(
                                chat_id=chat_id,
                                original_exc=exc,
                                task=task,
                            ) from exc
                        break
                    logging.warning(
                        "Failed to send telegram report to chat %s (%s) (attempt %s/%s): %s",
                        chat_id,
                        method,
                        attempt,
                        retries,
                        _format_exc(exc),
                    )
                    delay_idx = max(0, attempt - 1)
                    delay = retry_delays[min(delay_idx, len(retry_delays) - 1)]
                    await asyncio.sleep(delay)
                except Exception as exc:
                    logging.error(
                        "Unexpected error while sending telegram report to chat %s (%s): %s",
                        chat_id,
                        method,
                        _format_exc(exc),
                    )
                    if raise_on_fail:
                        raise TelegramDeliveryError(chat_id=chat_id, original_exc=exc, task=task) from exc
                    break
    finally:
        if owns_session:
            await session.close()


async def get_balance_pic():
    from controllers.actions import Actions

    picture = await Actions.take_screenshot_of_region(
        WorkspaceCoords.BALANCE_WINDOW_TOP_LEFT, WorkspaceCoords.BALANCE_WINDOW_BOTTOM_RIGHT
    )
    buffer = BytesIO()
    picture.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


async def get_test_pic():
    from controllers.actions import Actions

    picture = await Actions.take_screenshot_of_region(
        WorkspaceCoords.WORKSPACE_TOP_LEFT, WorkspaceCoords.WORKSPACE_BOTTOM_RIGHT
    )
    buffer = BytesIO()
    picture.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer
