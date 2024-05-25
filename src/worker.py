import asyncio
import json
import logging.config

import redis.asyncio as redis

from config import get_logging_config
from controllers.actions import Actions
from controllers.requests import send_report
from controllers.window_checker import WindowChecker
from task_model import Task


async def execute_task(task: Task, redis_client: redis):
    logging.info(f"Executing task id {task.order_id} for {task.requisite} with amount {task.amount}")
    if await WindowChecker.check_transfer_section():
        await Actions.click_nickname_section()
        await Actions.enter_nickname(requisite='dnk-jarod')
        # await Actions.enter_nickname(requisite=task.requisite)
        await Actions.click_amount_section()
        await Actions.enter_amount(amount=str(1.00))
        if await WindowChecker.check_transfer_button():
            await Actions.click_transfer_button()
        if await WindowChecker.check_transfer_confirm_button():
            await Actions.click_transfer_confirm_button()

        task.status = 1 if await WindowChecker.check_confirm_transfer_section() else 0
    # logging.info(f"awaiting 30 seconds...")
    # await asyncio.sleep(30)
        await Actions.take_screenshot(task=task)
        # await send_report(task=task)
        serialized_task = json.dumps(task.dict())
        await redis_client.hset("tasks", task.order_id, serialized_task)

    else:
        await WindowChecker.check_logout()
        await WindowChecker.check_login()
        await WindowChecker.check_confirm_login()
        await WindowChecker.check_ad()
        await WindowChecker.check_cashier()

        await Actions.click_transfer_section()
        await Actions.click_nickname_section()
        await Actions.enter_nickname(requisite='dnk-jarod')
        await Actions.click_amount_section()
        await Actions.enter_amount(amount=str(1.00))

        if await WindowChecker.check_transfer_button():
            await Actions.click_transfer_button()
        if await WindowChecker.check_transfer_confirm_button():
            await Actions.click_transfer_confirm_button()

        task.status = 1 if await WindowChecker.check_confirm_transfer_section() else 0

        await Actions.take_screenshot(task=task)
        # await send_report(task=task)
        serialized_task = json.dumps(task.dict())
        await redis_client.hset("tasks", task.order_id, serialized_task)


async def main():
    redis_client = redis.Redis(db=10)
    await asyncio.sleep(3)

    logging_config = get_logging_config('worker')
    logging.config.dictConfig(logging_config)
    logging.info("Waiting for tasks...")

    while True:
        _, task_data = await redis_client.brpop('queue')
        task = Task.parse_raw(task_data.decode('utf-8'))
        await execute_task(task, redis_client)


if __name__ == "__main__":
    asyncio.run(main())
