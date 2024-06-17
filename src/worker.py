import asyncio
from datetime import datetime
import logging.config

import redis.asyncio as redis

from config import get_logging_config
from controllers.actions import Actions
from controllers.processing import check_timer, execute_task
from controllers.window_checker import WindowChecker
from task_model import Task

start_cycle_time = None


async def handle_timeout():
    logging.info("Global timeout reached 50 minutes. Performing scheduled actions...")
    if await WindowChecker.check_close_cashier_button():
        await Actions.tab_clicking()
        await WindowChecker.check_cashier()
        if await WindowChecker.check_cashier_fullscreen_button():
            await Actions.click_transfer_section()

    global start_cycle_time
    start_cycle_time = datetime.now()

    logging.info((start_cycle_time.strftime("%H:%M:%S")), "Refreshing global timer on 50 minutes, returning to tasks...")


async def main():
    redis_client = redis.Redis(db=10)
    logging_config = get_logging_config('worker')
    logging.config.dictConfig(logging_config)

    await asyncio.sleep(4)
    global start_cycle_time
    start_cycle_time = datetime.now()
    last_activity_time = start_cycle_time
    logging.info((start_cycle_time.strftime("%H:%M:%S")), "Worker started, setting up global timer on 50 minutes...")

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
