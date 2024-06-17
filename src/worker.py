import asyncio
from datetime import datetime, timedelta
import json
import logging.config

import redis.asyncio as redis

from config import get_logging_config, settings
from controllers.actions import Actions
from controllers.requests import send_report
from controllers.window_checker import WindowChecker
from task_model import Task

start_cycle_time = None


async def check_timer(last_activity_time, start_time):
    current_time = datetime.now()
    if current_time - last_activity_time >= timedelta(minutes=50):
        await handle_timeout()
        return current_time
    if current_time - start_time >= timedelta(minutes=50):
        await handle_timeout()
        return current_time
    return last_activity_time


async def handle_timeout():
    logging.info("Global timeout reached 50 minutes. Performing scheduled actions...")
    if await WindowChecker.check_close_cashier_button():
        await Actions.tab_clicking()
        await WindowChecker.check_cashier()
        if await WindowChecker.check_cashier_fullscreen_button():
            await Actions.click_transfer_section()

    global start_cycle_time
    start_cycle_time = datetime.now()

    logging.info(f'{start_cycle_time.strftime("%H:%M:%S")}. Refreshing global timer on 50 minutes, returning to tasks...')


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
            attempts += 1
            if await WindowChecker.check_close_cashier_button():
                await asyncio.sleep(2)
                await WindowChecker.check_cashier()
                if await WindowChecker.check_cashier_fullscreen_button():
                    await Actions.click_transfer_section()

            if attempts < settings.MAX_ATTEMPTS:
                await execute_task(task=task, redis_client=redis_client, attempts=attempts)
            else:
                await Actions.take_screenshot(task=task)
                logging.info(f"Task {task.order_id} failed after {attempts} attempts.")
                await send_report(task=task)


async def main():
    redis_client = redis.Redis(db=10)
    logging_config = get_logging_config('worker')
    logging.config.dictConfig(logging_config)

    await asyncio.sleep(4)
    global start_cycle_time
    start_cycle_time = datetime.now()
    last_activity_time = start_cycle_time
    logging.info(f'{start_cycle_time.strftime("%H:%M:%S")}. Worker started, setting up global timer on 50 minutes...')

    while True:
        # noinspection PyTypeChecker
        task_data = await redis_client.brpop('queue', timeout=5)
        if task_data:
            _, task_data = task_data
            task = Task.parse_raw(task_data.decode('utf-8'))
            await execute_task(task, redis_client)
            last_activity_time = datetime.now()
        last_activity_time = await check_timer(last_activity_time, start_cycle_time)


if __name__ == "__main__":
    asyncio.run(main())
