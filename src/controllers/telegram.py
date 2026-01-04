import asyncio
import logging
from io import BytesIO
from pathlib import Path

import aiofiles
from aiohttp import ClientError, ClientSession, ClientTimeout, FormData, TCPConnector
import socket

from internal.consts import WorkspaceCoords
from internal.schemas import Task


class TelegramDeliveryError(RuntimeError):
    def __init__(self, chat_id: int, original_exc: BaseException, task: Task | None = None):
        super().__init__(f"Failed to deliver telegram report to chat {chat_id}")
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
        for chat_id in chats:
            if image is not None:
                url = f"https://api.telegram.org/bot{token}/sendPhoto"
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
                url = f"https://api.telegram.org/bot{token}/sendMessage"

            for attempt in range(1, retries + 1):
                try:
                    if image is not None:
                        data = FormData()
                        data.add_field("chat_id", str(chat_id))
                        data.add_field("caption", text)
                        data.add_field("disable_notification", str(disable_notification).lower())
                        data.add_field("photo", img_bytes, filename=filename, content_type="image/png")
                    else:
                        data = {
                            "chat_id": str(chat_id),
                            "text": text,
                            "disable_notification": str(disable_notification).lower(),
                        }
                    async with session.post(url, data=data, ssl=False, timeout=timeout) as resp:
                        body = await resp.text()
                        if resp.status >= 400:
                            logging.error(
                                "Telegram API responded with status %s for chat %s: %s",
                                resp.status,
                                chat_id,
                                body,
                            )
                    break
                except (ClientError, asyncio.TimeoutError) as exc:
                    if attempt >= retries:
                        logging.error(
                            "Failed to send telegram report to chat %s after %s attempts: %s: %s",
                            chat_id,
                            retries,
                            type(exc).__name__,
                            exc,
                        )
                        if raise_on_fail:
                            raise TelegramDeliveryError(
                                chat_id=chat_id,
                                original_exc=exc,
                                task=task,
                            ) from exc
                        break
                    logging.warning(
                        "Failed to send telegram report to chat %s (attempt %s/%s): %s: %s",
                        chat_id,
                        attempt,
                        retries,
                        type(exc).__name__,
                        exc,
                    )
                    delay_idx = max(0, attempt - 1)
                    delay = retry_delays[min(delay_idx, len(retry_delays) - 1)]
                    await asyncio.sleep(delay)
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
