import asyncio
import json
import logging.config

import redis.asyncio as redis

from config import get_logging_config, settings
from controllers.actions import Actions
from controllers.requests import send_report
from controllers.window_checker import WindowChecker
from task_model import Task


async def handle_timeout():
    logging.info("No tasks for 20 minutes. Performing scheduled actions...")
    if await WindowChecker.check_close_cashier_button():
        await WindowChecker.check_cashier()
        if await WindowChecker.check_cashier_fullscreen_button():
            await Actions.click_transfer_section()
            return
    logging.info("Error occurred while performing scheduled actions...")


async def execute_task(task: Task, redis_client: redis, attempts: int = 0):
    logging.info(f"Executing task id {task.order_id} for {task.requisite} with amount {task.amount}")
    if await WindowChecker.check_transfer_section():
        await Actions.click_nickname_section()
        await Actions.enter_nickname(requisite=task.requisite)
        await Actions.click_amount_section()
        await Actions.enter_amount(amount=str(task.amount))
        if await WindowChecker.check_transfer_button():
            await Actions.click_transfer_button()
        if await WindowChecker.check_transfer_confirm_button():
            await Actions.click_transfer_confirm_button()

        task.status = 1 if await WindowChecker.check_confirm_transfer_section() else 0

        if task.status == 1:
            await Actions.take_screenshot(task=task)
            await send_report(task=task)
            serialized_task = json.dumps(task.dict())
            await redis_client.hset("tasks", task.order_id, serialized_task)
        else:
            await Actions.take_screenshot(task=task)
            attempts += 1
            if attempts < settings.MAX_ATTEMPTS:
                await execute_task(task=task, redis_client=redis_client, attempts=attempts)
            else:
                logging.info(f"Task {task.order_id} failed after {attempts} attempts.")
                await send_report(task=task)

    # else:
    #     await WindowChecker.check_logout()
    #     await WindowChecker.check_login()
    #     await WindowChecker.check_confirm_login()
    #     await WindowChecker.check_ad()
    #     await WindowChecker.check_cashier()
    #
    #     await Actions.click_transfer_section()
    #     await Actions.click_nickname_section()
    #     await Actions.enter_nickname(requisite=task.requisite)
    #     await Actions.click_amount_section()
    #     await Actions.enter_amount(amount=str(task.amount))
    #
    #     if await WindowChecker.check_transfer_button():
    #         await Actions.click_transfer_button()
    #     if await WindowChecker.check_transfer_confirm_button():
    #         await Actions.click_transfer_confirm_button()
    #
    #     task.status = 1 if await WindowChecker.check_confirm_transfer_section() else 0
    #
    #     await Actions.take_screenshot(task=task)
    #     await send_report(task=task)
    #     serialized_task = json.dumps(task.dict())
    #     await redis_client.hset("tasks", task.order_id, serialized_task)
    logging.info(f"Waiting for new tasks...")


async def main():
    redis_client = redis.Redis(db=10)
    await asyncio.sleep(3)

    logging_config = get_logging_config('worker')
    logging.config.dictConfig(logging_config)
    logging.info("Waiting for tasks...")

    while True:
        try:
            task_data = await asyncio.wait_for(redis_client.brpop('queue'), timeout=1200)
            _, task_data = task_data
            task = Task.parse_raw(task_data.decode('utf-8'))
            await execute_task(task, redis_client)
        except asyncio.TimeoutError:
            await handle_timeout()


if __name__ == "__main__":
    asyncio.run(main())
