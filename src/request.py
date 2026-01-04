import asyncio
from datetime import UTC, datetime
from http import HTTPStatus
from json import loads
import logging
import random

import aiohttp
from redis.asyncio import Redis
import redis.asyncio as redis

from controllers.crypt import Crypt
from internal.consts import RedisNames
from internal.schemas import ErrorType, Step, Task

logger = logging.getLogger(__name__)


def _trim_text(text: str | None, limit: int = 200) -> str:
    if not text:
        return ""
    return text if len(text) <= limit else f"{text[:limit]}..."


async def send_report(
    task: Task,
    redis_client: redis.Redis,
    settings,
    problem: str | None = None,
    retries: int = 3,
    retry_delays: tuple[float, ...] = (2.0, 5.0, 10.0),
) -> None:
    set_name = RedisNames.PROD_REPORTS
    if "dev-" in task.callback_url:
        set_name = RedisNames.DEV_REPORTS
    task.status = task.status if not problem else 0
    task.message = "" if not problem else problem
    async with aiohttp.ClientSession() as session:
        cryptor = Crypt(settings.key_encrypt, settings.key_decrypt)
        data_json = task.model_dump_json()
        data = {
            "order_id": task.order_id,
            "user_id": task.user_id,
            "requisite": task.requisite,
            "amount": task.amount,
            "status": task.status,
            "message": task.message,
            "callback_url": task.callback_url,
            "step": task.step,
        }
        headers = {"x-simpleex-sign": cryptor.encrypt(data_json)}
        text_ok = f"Report sent: {task.order_id}|{task.user_id}|{task.requisite}|${task.amount}|{task.status}"
        last_status = None
        last_error = None
        for attempt in range(retries):
            try:
                async with session.post(task.callback_url, data=data, headers=headers) as response:
                    if response.status == HTTPStatus.OK:
                        task.step = Step.REPORTED
                        await redis_client.lpush(set_name, task.model_dump_json())
                        logger.info(text_ok)
                        return
                    else:
                        task.step = Step.REPORT_FAILED
                        await redis_client.lpush(set_name, task.model_dump_json())
                        last_status = response.status
                        last_error = await response.text()
            except Exception as e:
                last_error = f"{type(e).__name__}: {e}"

            if attempt < retries - 1:
                delay = retry_delays[min(attempt, len(retry_delays) - 1)]
                await asyncio.sleep(delay)
    if last_status is not None:
        logger.warning(
            "Report failed after %s attempts: task_id=%s status=%s error=%s",
            retries,
            task.order_id,
            last_status,
            _trim_text(last_error),
        )
    else:
        logger.warning(
            "Report failed after %s attempts: task_id=%s error=%s",
            retries,
            task.order_id,
            _trim_text(last_error),
        )


async def send_error_report(
    task: Task,
    error_type: ErrorType,
    settings,
    retries: int = 3,
    retry_delays: tuple[float, ...] = (2.0, 5.0, 10.0),
) -> None:
    now = datetime.now(UTC)
    async with aiohttp.ClientSession() as session:
        cryptor = Crypt(settings.key_encrypt, settings.key_decrypt)
        data_json = task.model_dump_json()
        data = {
            "appName": "pokerok_app",
            "type": error_type,
            "payload": data_json,
            "timestamp": now,
        }
        headers = {"x-simpleex-sign": cryptor.encrypt(data_json)}
        text_ok = f"Error report sent: {task.order_id}|{task.user_id}|{task.requisite}|${task.amount}|{task.status}"
        last_status = None
        last_error = None
        for attempt in range(retries):
            try:
                async with session.post(task.callback_url, data=data, headers=headers) as response:
                    if response.status == HTTPStatus.OK:
                        logger.info(text_ok)
                        return
                    else:
                        last_status = response.status
                        last_error = await response.text()
            except Exception as e:
                last_error = f"{type(e).__name__}: {e}"

            if attempt < retries - 1:
                delay = retry_delays[min(attempt, len(retry_delays) - 1)]
                await asyncio.sleep(delay)
    if last_status is not None:
        logger.warning(
            "Error report failed after %s attempts: task_id=%s status=%s error=%s",
            retries,
            task.order_id,
            last_status,
            _trim_text(last_error),
        )
    else:
        logger.warning(
            "Error report failed after %s attempts: task_id=%s error=%s",
            retries,
            task.order_id,
            _trim_text(last_error),
        )


async def add_test_task(redis_client: Redis):
    task = Task(
        order_id=7000000 + random.randint(0, 999999),
        user_id=13,
        requisite="SimpleEx1",
        amount=1.11,
        status=0,
        callback_url="https://dev-xyz.simpleex.store/api/v2/fer/callback",
    )
    await redis_client.rpush(RedisNames.QUEUE, task.model_dump_json())


async def extract_requisites(redis_client: Redis):
    items = await redis_client.lrange(RedisNames.PROD_REPORTS, 0, -1)
    requisites = set()
    for item in items:
        try:
            data = loads(item)
            if "requisite" in data:
                requisites.add(data["requisite"])
        except:
            continue

    if requisites:
        await redis_client.sadd(RedisNames.REQUISITES, *requisites)
        logging.info(f"Successfully extracted {len(requisites)} requisites")
    else:
        logging.info("No requisites found")


def run_main():
    from config import settings

    async def _run():
        async with redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD.get_secret_value(),
        ) as redis_client:
            await add_test_task(redis_client)

    asyncio.run(_run())


if __name__ == "__main__":
    run_main()
