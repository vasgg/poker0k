import asyncio
import logging

import aiohttp

from config import settings
from controllers.crypt import Crypt
from enums import Task

logger = logging.getLogger(__name__)


async def send_report(task: Task, status: int = 1) -> None:
    async with aiohttp.ClientSession() as session:
        cryptor = Crypt(settings.key_encrypt, settings.key_decrypt)
        url = settings.REPORT_ENDPOINT
        data_json = task.model_dump_json()
        data = {
            'order_id': task.order_id,
            'user_id': task.user_id,
            'requisite': task.requisite,
            'amount': task.amount,
            'status': task.status
        }
        headers = {'x-simpleex-sign': cryptor.encrypt(data_json)}
        suffix = 'SUCCESS' if status == 1 else 'FAIL'
        text_ok = f'report sent: {task.order_id}|{task.user_id}|{task.requisite}|${task.amount}|{suffix}'
        text_not_ok = f'report sent: {task.order_id}|{task.user_id}|{task.requisite}|${task.amount}|{suffix} with response: ' + '{}. {}'

        async with session.post(url, data=data, headers=headers) as response:
            if response.status == 200:
                logger.info(text_ok)
                print(await response.json())
            else:
                error_text = await response.text()
                logger.info(text_not_ok.format(response.status, error_text))
                print(await response.json())
    print(data)


async def send_queue_request() -> None:
    async with aiohttp.ClientSession() as session:
        url = 'http://188.127.243.64:8800/queue_length/'
        async with session.get(url) as response:
            if response.status == 200:
                print(await response.json())
            else:
                print(await response.json())


def run_main():
    # asyncio.run(send_report(task=Task(order_id=1, user_id=1, requisite='Mein Herz Brent', amount=1.00, status=1)))
    asyncio.run(send_queue_request())


if __name__ == '__main__':
    run_main()
