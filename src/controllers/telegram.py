from http import HTTPStatus
from pathlib import Path
import logging.config

import aiofiles
import aiohttp
from aiohttp import FormData

from config import settings
from internal import Task

# logging_config = get_logging_config('tg_reporter')
# logging.config.dictConfig(logging_config)


async def send_telegram_report(task: Task, message: str, image_path: Path | None = None) -> None:
    if image_path:
        url = f"https://api.telegram.org/bot{settings.TG_BOT_TOKEN.get_secret_value()}/sendPhoto"
        data = FormData()
        data.add_field('chat_id', f'{settings.TG_ID}')
        data.add_field('caption', f'{task.order_id}|{task.requisite}|${task.amount}|{message}')
        data.add_field('disable_notification', False)
        async with aiofiles.open(image_path, 'rb') as photo:
            photo_data = await photo.read()
            data.add_field('photo', photo_data, filename=image_path.name)
        # text_ok = f'TG report sent with screenshot {image_path.name}.'
        # text_not_ok = f'TG report sent with screenshot {image_path.name} FAILED with response:'
    else:
        url = f"https://api.telegram.org/bot{settings.TG_BOT_TOKEN.get_secret_value()}/sendMessage"
        data = {
            'chat_id': f'{settings.TG_ID}',
            'text': f'{task.order_id}|{task.requisite}|${task.amount}|{message}',
            'disable_notification': False,
        }
        # text_ok = f'TG report sent.'
        # text_not_ok = f'TG report FAILED with response:'

    async with aiohttp.ClientSession() as session:
        await session.post(url, data=data, ssl=False)
        # async with session.post(url, data=data) as response:
        #     if response.status == HTTPStatus.OK:
        #         logging.info(text_ok)
        #     else:
        #         error_text = await response.text()
        #         logging.info(f"{text_not_ok} {response.status}. {error_text}")
