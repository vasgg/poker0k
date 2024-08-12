import asyncio
import json
import logging.config

from pynput.mouse import Controller
import redis.asyncio as redis

from config import get_logging_config, settings
from consts import Coords
from controllers.actions import Actions
from controllers.requests import send_report
from controllers.window_checker import WindowChecker
from internal import Task


async def execute_task(task: Task, redis_client: redis, mouse: Controller, attempts: int = 0):
    await asyncio.sleep(3)
    logging.info(f"Executing task id {task.order_id} for {task.requisite} with amount {task.amount}")

    await Actions.mouse_click(mouse, Coords.ANDROID_NICKNAME_SECTION, 3)
    await Actions.enter_nickname(requisite=task.requisite)
    await Actions.mouse_click(mouse, Coords.ANDROID_AMOUNT_SECTION, 3)
    await Actions.enter_amount(amount=str(task.amount).replace('.', ','))
    await Actions.mouse_click(mouse, Coords.ANDROID_TRANSFER_BUTTON, 3)
    if await WindowChecker.check_transfer_confirm_button():
        await Actions.mouse_click(mouse, Coords.ANDROID_TRANSFER_CONFIRM_BUTTON, 1)

        task.status = 1 if await WindowChecker.check_confirm_transfer_section() else 0

        if task.status == 1:
            await Actions.take_screenshot(task=task)
            # await send_report(task=task)
            # serialized_task = json.dumps(task.model_dump())
            # await redis_client.hset('tasks', task.order_id, serialized_task)
            await redis_client.lpush('records', task.model_dump_json())
        else:
            attempts += 1
            await Actions.take_screenshot(task=task, debug=True)
            if await WindowChecker.check_close_cashier_button():
                await asyncio.sleep(2)
                await WindowChecker.check_cashier()
                if await WindowChecker.check_cashier_fullscreen_button():
                    await Actions.click_transfer_section()
            else:
                await send_report(task=task, problem=f'Cashier did not closed after timeout. Check Cashier window.')
                return

            if attempts < settings.MAX_ATTEMPTS:
                await execute_task(task=task, redis_client=redis_client, attempts=attempts)
            else:
                await Actions.take_screenshot(task=task)
                logging.info(f"Task {task.order_id} failed after {attempts} attempts.")
                await send_report(task=task)

    else:
        await send_report(
            task=task,
            problem=f'Transfer to {task.requisite} with amount {task.amount} failed. Check Cashier window or transfer section.',
        )


async def main():
    redis_client = redis.Redis(db=10)
    logging_config = get_logging_config('worker_android')
    logging.config.dictConfig(logging_config)
    mouse = Controller()

    await asyncio.sleep(4)
    logging.info(f'Worker started...')

    while True:
        # noinspection PyTypeChecker
        task_data = await redis_client.brpop('queue', timeout=5)
        if task_data:
            _, task_data = task_data
            task = Task.model_validate_json(task_data.decode('utf-8'))
            await execute_task(task, redis_client, mouse)


def run_main():
    asyncio.run(main())


if __name__ == '__main__':
    run_main()
