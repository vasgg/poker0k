from io import BytesIO
from pathlib import Path

import aiofiles
from aiohttp import FormData, ClientSession

from config import settings
from controllers.actions import Actions
from internal.consts import WorkspaceCoords
from internal.schemas import Task


async def send_telegram_report(
    message: str,
    chats: tuple,
    task: Task | None = None,
    image: Path | BytesIO | bytes | None = None,
    disable_notification: bool = False,
) -> None:
    text = f"{task.order_id}|{task.requisite}|${task.amount}|{message}" if task else message
    token = settings.TG_BOT_TOKEN.get_secret_value()

    for chat_id in chats:
        if image is not None:
            url = f"https://api.telegram.org/bot{token}/sendPhoto"
            data = FormData()
            data.add_field("chat_id", str(chat_id))
            data.add_field("caption", text)
            data.add_field("disable_notification", str(disable_notification).lower())

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

            data.add_field("photo", img_bytes, filename=filename, content_type="image/png")
        else:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            data = {
                "chat_id": str(chat_id),
                "text": text,
                "disable_notification": str(disable_notification).lower(),
            }

        async with ClientSession() as session:
            await session.post(url, data=data, ssl=False)


async def get_balance_pic():
    picture = await Actions.take_screenshot_of_region(
        WorkspaceCoords.BALANCE_WINDOW_TOP_LEFT, WorkspaceCoords.BALANCE_WINDOW_BOTTOM_RIGHT
    )
    buffer = BytesIO()
    picture.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer
