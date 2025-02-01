from pathlib import Path

import aiofiles
import aiohttp
from aiohttp import FormData
from requests import get

from config import settings
from internal import Task


async def send_telegram_report(message: str, task: Task | None = None, image_path: Path | None = None) -> None:
    text = f"{task.order_id}|{task.requisite}|${task.amount}|{message}" if task else message
    if image_path:
        url = f"https://api.telegram.org/bot{settings.TG_BOT_TOKEN.get_secret_value()}/sendPhoto"
        data = FormData()
        data.add_field("chat_id", f"{settings.TG_ID}")
        data.add_field("caption", text)
        data.add_field("disable_notification", "false")
        async with aiofiles.open(image_path, "rb") as photo:
            photo_data = await photo.read()
            data.add_field("photo", photo_data, filename=image_path.name)

    else:
        url = f"https://api.telegram.org/bot{settings.TG_BOT_TOKEN.get_secret_value()}/sendMessage"
        data = {
            "chat_id": f"{settings.TG_ID}",
            "text": text,
            "disable_notification": False,
        }

    async with aiohttp.ClientSession() as session:
        await session.post(url, data=data, ssl=False)


def send_report_at_exit():
    url = (
        f"https://api.telegram.org/bot{settings.TG_BOT_TOKEN.get_secret_value()}"
        f"/sendMessage?text=Worker stopped&chat_id={settings.TG_ID}"
    )
    get(url)
