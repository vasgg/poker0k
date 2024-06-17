import asyncio
from datetime import datetime, timedelta
import json
import logging

from redis import asyncio as redis

from config import settings
from controllers.actions import Actions
from controllers.requests import send_report
from controllers.window_checker import WindowChecker
from task_model import Task
from worker import handle_timeout

logger = logging.getLogger(__name__)


async def execute_task(task: Task, redis_client: redis, attempts: int = 0):
    logger.info(f"Executing task id {task.order_id} for {task.requisite} with amount {task.amount}")
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
                logger.info(f"Task {task.order_id} failed after {attempts} attempts.")
                await send_report(task=task)


async def check_timer(last_activity_time, start_time):
    current_time = datetime.now()
    if current_time - last_activity_time >= timedelta(minutes=50):
        await handle_timeout()
        return current_time
    if current_time - start_time >= timedelta(minutes=50):
        await handle_timeout()
        return current_time
    return last_activity_time
