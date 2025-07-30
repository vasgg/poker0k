import asyncio
from datetime import UTC, datetime
from http import HTTPStatus
from json import JSONDecodeError, loads
import logging
import random

import aiohttp
from redis.asyncio import Redis
import redis.asyncio as redis

from controllers.actions import blink, send_update
from controllers.crypt import Crypt
from internal.consts import RedisNames
from internal.schemas import ErrorType, Step, Task

logger = logging.getLogger(__name__)


async def send_report(
    task: Task,
    redis_client: redis.Redis,
    settings,
    problem: str | None = None,
    retries: int = 3,
    delay: int = 3,
) -> None:
    set_name = "prod_reports"
    if "dev-" in task.callback_url:
        set_name = "dev_reports"
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
        text_not_ok = (
            f"Report sent: {task.order_id}|{task.user_id}|{task.requisite}|${task.amount}|{task.status} with response:"
        )
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
                        error_text = await response.text()
                        logger.info(f"{text_not_ok} {response.status}. {error_text}")
            except Exception as e:
                logger.exception(f"Attempt {attempt + 1} failed with error: {e}")

            if attempt < retries - 1:
                await asyncio.sleep(delay)
    logger.exception(f"Failed to send report after {retries} attempts, task id: {task.order_id} failed with error")


async def send_error_report(task: Task, error_type: ErrorType, settings, retries: int = 3, delay: int = 3) -> None:
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
        text_not_ok = f"Error report sent: {task.order_id}|{task.user_id}|{task.requisite}|${task.amount}|{task.status} with response:"
        for attempt in range(retries):
            try:
                async with session.post(task.callback_url, data=data, headers=headers) as response:
                    if response.status == HTTPStatus.OK:
                        logger.info(text_ok)
                        return
                    else:
                        error_text = await response.text()
                        logger.info(f"{text_not_ok} {response.status}. {error_text}")
            except Exception as e:
                logger.exception(f"Attempt {attempt + 1} failed with error: {e}")

            if attempt < retries - 1:
                await asyncio.sleep(delay)
    logger.exception(f"Failed to send error report after {retries} attempts, task id: {task.order_id} failed.")


async def add_test_task(redis_client: redis.Redis):
    task = Task(
        order_id=1000000 + random.randint(0, 999999),
        user_id=13,
        requisite="dnk-jarod",
        amount=1.11,
        status=0,
        callback_url="https://dev-xyz.simpleex.store/api/v2/fer/callback",
    )
    await redis_client.rpush(RedisNames.QUEUE, task.model_dump_json())


async def get_all_requisites(redis_client: Redis, set_name: str) -> set[str]:
    requisites = set()
    try:
        key_type = await redis_client.type(set_name)
        if key_type != "set":
            logger.error(f"Key {set_name} is of type {key_type}, expected 'set'")
            return requisites

        members = await redis_client.smembers(set_name)

        for item in members:
            try:
                data = loads(item)
                if 'requisite' in data:
                    requisites.add(data['requisite'])
            except JSONDecodeError:
                logger.warning(f"Invalid JSON in Redis set: {item}")
                continue
        return requisites

    except Exception as e:
        logger.exception(f"Failed to get requisites from Redis: {e}")
        return set()


async def redis_routine(redis_client: Redis):
    try:
        requisites = await get_all_requisites(redis_client, RedisNames.PROD_REPORTS)
        logger.info(f"Found {len(requisites)} requisites in Redis")

        if not requisites:
            logger.info("No requisites found to save")
        req_type = await redis_client.type(RedisNames.REQUISITES)
        if req_type != "set":
            await redis_client.delete(RedisNames.REQUISITES)

        await redis_client.sadd(RedisNames.REQUISITES, *requisites)
        logger.info(f"Requisites saved to {RedisNames.REQUISITES}")

        count = await redis_client.scard(RedisNames.REQUISITES)
        logger.info(f"Requisites count: {count}")

    except Exception as e:
        logger.exception(f"Error in redis_routine: {e}")
        raise


def run_main():
    from config import settings

    redis_client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        password=settings.REDIS_PASSWORD.get_secret_value(),
    )
    # asyncio.run(add_test_task(redis_client))
    asyncio.run(blink('red'))
    asyncio.run(redis_routine(redis_client))


if __name__ == "__main__":
    run_main()
