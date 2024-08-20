import asyncio
from http import HTTPStatus
import logging

import aiohttp

from config import settings
from controllers.crypt import Crypt
from internal import Step, Task
from redis.asyncio import Redis

logger = logging.getLogger(__name__)


async def send_report(task: Task, redis_client: Redis, problem: str | None = None, retries: int = 3, delay: int = 3) -> None:
    async with aiohttp.ClientSession() as session:
        cryptor = Crypt(settings.key_encrypt, settings.key_decrypt)
        data_json = task.model_dump_json()
        data = {
            'order_id': task.order_id,
            'user_id': task.user_id,
            'requisite': task.requisite,
            'amount': task.amount,
            'status': task.status if not problem else 2,
            'message': '' if not problem else problem,
            'callback_url': task.callback_url,
            'step': task.step,
        }
        headers = {'x-simpleex-sign': cryptor.encrypt(data_json)}
        text_ok = f'report sent: {task.order_id}|{task.user_id}|{task.requisite}|${task.amount}|{task.status}'
        text_not_ok = f'report sent: {task.order_id}|{task.user_id}|{task.requisite}|${task.amount}|{task.status} with response:'
        for attempt in range(retries):
            try:
                async with session.post(task.callback_url, data=data, headers=headers) as response:
                    if response.status == HTTPStatus.OK:
                        task.step = Step.REPORTED
                        await redis_client.lpush('reports', task.model_dump_json())
                        logger.info(text_ok)
                        return
                    else:
                        task.step = Step.REPORT_FAILED
                        await redis_client.lpush('reports', task.model_dump_json())
                        error_text = await response.text()
                        logger.info(f"{text_not_ok} {response.status}. {error_text}")
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed with error: {e}")

            if attempt < retries - 1:
                await asyncio.sleep(delay)
    logger.error(f"Failed to send report after {retries} attempts, task id: {task.order_id} failed with error")


async def send_queue_request() -> None:
    async with aiohttp.ClientSession() as session:
        async with session.post(url=f'{settings.TEST_ENDPOINT}/queue_length/') as response:
            logger.info(await response.json())


async def send_task_request() -> None:
    async with aiohttp.ClientSession() as session:
        async with session.post(url=f'{settings.TEST_ENDPOINT}/add_task/') as response:
            logger.info(await response.json())


def run_main():
    # asyncio.run(send_report(task=Task(order_id=1, user_id=1, requisite='Mein Herz Brent', amount=1.00, status=1)))
    asyncio.run(send_queue_request())
    # asyncio.run(send_task_request())


if __name__ == '__main__':
    run_main()
