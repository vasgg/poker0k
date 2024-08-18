import asyncio
import logging.config

from pynput.mouse import Controller
import redis.asyncio as redis

from config import get_logging_config, settings
from consts import Colors, Coords
from controllers.actions import Actions
from controllers.requests import send_report
from internal import Step, Task


async def execute_task(task: Task, redis_client: redis, mouse: Controller, attempts: int = 0):
    await asyncio.sleep(3)
    logging.info(f"Executing task id {task.order_id} for {task.requisite} with amount {task.amount}")
    await Actions.click_on_const(mouse, Coords.ANDROID_NICKNAME_SECTION, 3)
    await Actions.enter_nickname(requisite=task.requisite)
    await Actions.click_on_const(mouse, Coords.ANDROID_AMOUNT_SECTION, 3)
    await Actions.enter_amount(amount=str(task.amount).replace('.', ','))

    workspace = await Actions.take_screenshot_of_region(Actions.WORKSPACE_TOP_LEFT, Actions.WORKSPACE_BOTTOM_RIGHT)
    transfer_button = await Actions.find_color_square(image=workspace, color=Colors.ANDROID_GREEN, tolerance_percent=10)
    if transfer_button:
        await Actions.click_on_finded(mouse, transfer_button, 'TRANSFER BUTTON')
    else:
        logging.info(f"Task {task.order_id} failed... Can't find transfer button")

    workspace = await Actions.take_screenshot_of_region(Actions.WORKSPACE_TOP_LEFT, Actions.WORKSPACE_BOTTOM_RIGHT)
    transfer_confirm_button = await Actions.find_color_square(image=workspace, color=Colors.ANDROID_GREEN, tolerance_percent=10)
    if transfer_confirm_button:
        await Actions.click_on_finded(mouse, transfer_confirm_button, 'TRANSFER CONFIRM BUTTON')
    else:
        logging.info(f"Task {task.order_id} failed... Can't find transfer confirm button")

    workspace = await Actions.take_screenshot_of_region(Actions.WORKSPACE_TOP_LEFT, Actions.WORKSPACE_BOTTOM_RIGHT)
    transfer_confirm_section = await Actions.find_color_square(image=workspace, color=Colors.FINAL_GREEN, tolerance_percent=10)
    task.status = 1 if transfer_confirm_section else 0
    if task.status == 1:
        task.step = Step.PROCESSED
        await redis_client.lpush('reports', task.model_dump_json())
        await Actions.take_screenshot(task=task)
        await send_report(task=task, redis_client=redis_client)
    else:
        task.step = Step.FAILED
        await redis_client.lpush('reports', task.model_dump_json())
        attempts += 1
        await Actions.take_screenshot(task=task, debug=True)
        logging.info(f"Task {task.order_id} failed... Can't find transfer confirm section")
        if attempts < settings.MAX_ATTEMPTS:
            await execute_task(task=task, redis_client=redis_client, mouse=mouse, attempts=attempts)
        else:
            await Actions.take_screenshot(task=task)
            logging.info(f"Task {task.order_id} failed after {attempts} attempts.")
            await send_report(
                task=task,
                redis_client=redis_client,
                problem=f'Transfer to {task.requisite} with amount {task.amount} failed. Please check the app...',
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
