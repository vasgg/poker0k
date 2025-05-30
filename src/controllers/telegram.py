from pathlib import Path

import aiofiles
from aiohttp import FormData, ClientSession

from config import settings
from internal.schemas import Task


async def send_telegram_report(
    message: str,
    task: Task | None = None,
    image_path: Path | None = None,
    disable_notification: bool = False,
    verbose: bool = True,
) -> None:
    text = f"{task.order_id}|{task.requisite}|${task.amount}|{message}" if task else message
    chats = [settings.TG_REPORTS_CHAT, settings.TG_BOT_ADMIN_ID] if verbose else [settings.TG_BOT_ADMIN_ID]
    for chat_id in chats:
        if image_path:
            url = f"https://api.telegram.org/bot{settings.TG_BOT_TOKEN.get_secret_value()}/sendPhoto"
            data = FormData()
            data.add_field("chat_id", f"{chat_id}")
            data.add_field("caption", text)
            data.add_field("disable_notification", (str(disable_notification)).lower())
            async with aiofiles.open(image_path, "rb") as photo:
                photo_data = await photo.read()
                data.add_field("photo", photo_data, filename=image_path.name)

        else:
            url = f"https://api.telegram.org/bot{settings.TG_BOT_TOKEN.get_secret_value()}/sendMessage"
            data = {
                "chat_id": f"{chat_id}",
                "text": text,
                "disable_notification": False,
            }

        async with ClientSession() as session:
            await session.post(url, data=data, ssl=False)
