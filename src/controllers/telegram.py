import asyncio
import logging
from io import BytesIO
from pathlib import Path

import aiofiles
from aiohttp import ClientError, ClientSession, ClientTimeout, FormData

from internal.consts import WorkspaceCoords
from internal.schemas import Task

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT = ClientTimeout(total=20, connect=10)


async def send_telegram_report(
    message: str,
    chats: tuple,
    task: Task | None = None,
    image: Path | BytesIO | bytes | None = None,
    disable_notification: bool = False,
    retries: int = 3,
    retry_delay: float = 2,
    timeout: ClientTimeout | None = None,
) -> None:
    from config import settings

    text = f"{task.order_id}|{task.requisite}|${task.amount}|{message}" if task else message
    token = settings.TG_BOT_TOKEN.get_secret_value()

    image_bytes: bytes | None = None
    image_filename: str | None = None

    if image is not None:
        if isinstance(image, Path):
            async with aiofiles.open(image, "rb") as f:
                image_bytes = await f.read()
            image_filename = image.name
        elif isinstance(image, BytesIO):
            image_bytes = image.getvalue()
            image_filename = "screenshot.png"
        elif isinstance(image, (bytes, bytearray)):
            image_bytes = bytes(image)
            image_filename = "screenshot.png"
        else:
            raise ValueError("Unsupported image type")

    timeout = timeout or _DEFAULT_TIMEOUT

    async with ClientSession(timeout=timeout) as session:
        for chat_id in chats:
            for attempt in range(1, retries + 1):
                try:
                    if image_bytes is not None and image_filename is not None:
                        url = f"https://api.telegram.org/bot{token}/sendPhoto"
                        data = FormData()
                        data.add_field("chat_id", str(chat_id))
                        data.add_field("caption", text)
                        data.add_field("disable_notification", str(disable_notification).lower())
                        data.add_field("photo", image_bytes, filename=image_filename, content_type="image/png")
                    else:
                        url = f"https://api.telegram.org/bot{token}/sendMessage"
                        data = {
                            "chat_id": str(chat_id),
                            "text": text,
                            "disable_notification": str(disable_notification).lower(),
                        }

                    async with session.post(url, data=data, ssl=False) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            raise RuntimeError(
                                f"Telegram API responded with status {response.status}: {error_text}"
                            )
                    break
                except (asyncio.TimeoutError, ClientError, RuntimeError) as exc:
                    logger.warning(
                        "Failed to send Telegram report to chat %s (attempt %s/%s): %s",
                        chat_id,
                        attempt,
                        retries,
                        exc,
                    )
                    if attempt == retries:
                        logger.exception("Giving up sending Telegram report to chat %s", chat_id)
                    else:
                        await asyncio.sleep(retry_delay)
                        continue
                except Exception:
                    logger.exception("Unexpected error while sending Telegram report to chat %s", chat_id)
                    break


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
