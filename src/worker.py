import asyncio
from datetime import timedelta, timezone, datetime
import logging.config

from pynput.mouse import Controller
import redis.asyncio as redis

from config import get_logging_config, settings
from consts import Colors, Coords
from controllers.actions import Actions
from controllers.requests import send_report
from internal import Step, Task


start_cycle_time = None


async def check_timer(last_activity_time, start_time, mouse: Controller):
    current_time = datetime.now(timezone(timedelta(hours=3)))
    if current_time - last_activity_time >= timedelta(hours=23):
        await handle_timeout(mouse)
        return current_time
    if current_time - start_time >= timedelta(hours=23):
        await handle_timeout(mouse)
        return current_time
    return last_activity_time


async def handle_timeout(mouse: Controller):
    logging.info("Global timeout reached 23 hours. Performing scheduled actions.")
    await Actions.click_on_const(mouse, Coords.ANDROID_CLOSE_EMULATOR_BUTTON, 3)
    workspace = await Actions.take_screenshot_of_region(Actions.WORKSPACE_TOP_LEFT, Actions.WORKSPACE_BOTTOM_RIGHT)
    transfer_button = await Actions.find_color_square(
        image=workspace, color=Colors.ANDROID_CLOSE_BUTTON_COLOR, tolerance_percent=10
    )
    if transfer_button:
        await Actions.click_on_finded(mouse, transfer_button, 'CONFIRM EXIT BUTTON')
    else:
        logging.info("Error. Can't find CONFIRM EXIT BUTTON")
    await Actions.click_on_const(mouse, Coords.ANDROID_OPEN_EMULATOR_BUTTON)
    await Actions.click_on_const(mouse, Coords.ANDROID_OPEN_EMULATOR_BUTTON, 180)
    await Actions.click_on_const(mouse, Coords.ANDROID_DONT_SHOW_TODAY, 5)
    await Actions.click_on_const(mouse, Coords.ANDROID_ME_SECTION, 10)
    await Actions.click_on_const(mouse, Coords.ANDROID_CASHIER_BUTTON, 10)
    await Actions.click_on_const(mouse, Coords.ANDROID_CASHIER_SETTINGS, 10)
    await Actions.click_on_const(mouse, Coords.ANDROID_TRANSFER_SECTION, 10)

    global start_cycle_time
    start_cycle_time = datetime.now(timezone(timedelta(hours=3)))
    logging.info('Reset global timer on 23 hours, returning to tasks.')


async def execute_task(task: Task, redis_client: redis, mouse: Controller, attempts: int = 0):
    await asyncio.sleep(3)
    logging.info(f"Executing task id {task.order_id} for {task.requisite} with amount {task.amount}")
    await Actions.click_on_const(mouse, Coords.ANDROID_NICKNAME_SECTION, 3)
    await Actions.input_value(value=task.requisite)
    await Actions.click_on_const(mouse, Coords.ANDROID_AMOUNT_SECTION, 3)
    await Actions.input_value(value=str(task.amount).replace('.', ','))

    workspace = await Actions.take_screenshot_of_region(Actions.WORKSPACE_TOP_LEFT, Actions.WORKSPACE_BOTTOM_RIGHT)
    transfer_button = await Actions.find_color_square(image=workspace, color=Colors.ANDROID_GREEN, tolerance_percent=10)
    if transfer_button:
        await Actions.click_on_finded(mouse, transfer_button, 'TRANSFER BUTTON')
    else:
        logging.info(f"Task {task.order_id} failed. Can't find transfer button.")

    workspace = await Actions.take_screenshot_of_region(Actions.WORKSPACE_TOP_LEFT, Actions.WORKSPACE_BOTTOM_RIGHT)
    transfer_confirm_button = await Actions.find_color_square(
        image=workspace, color=Colors.ANDROID_GREEN, tolerance_percent=10
    )
    if transfer_confirm_button:
        await Actions.click_on_finded(mouse, transfer_confirm_button, 'TRANSFER CONFIRM BUTTON')
    else:
        logging.info(f"Task {task.order_id} failed. Can't find transfer confirm button.")

    workspace = await Actions.take_screenshot_of_region(Actions.WORKSPACE_TOP_LEFT, Actions.WORKSPACE_BOTTOM_RIGHT)
    transfer_confirm_section = await Actions.find_color_square(
        image=workspace, color=Colors.FINAL_GREEN, tolerance_percent=10
    )
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
        logging.info(f"Task {task.order_id} failed. Can't find transfer confirm section.")
        if attempts < settings.MAX_ATTEMPTS:
            await execute_task(task=task, redis_client=redis_client, mouse=mouse, attempts=attempts)
        else:
            await Actions.take_screenshot(task=task)
            logging.info(f"Task {task.order_id} failed after {attempts} attempts.")
            await send_report(
                task=task,
                redis_client=redis_client,
                problem=f'Transfer to {task.requisite} with amount {task.amount} failed. Please check the app.',
            )


async def main():
    redis_client = redis.Redis(db=10)
    logging_config = get_logging_config('worker_android')
    logging.config.dictConfig(logging_config)
    logging.info(f'Worker started. Restart after 23 hours.')
    mouse = Controller()
    await asyncio.sleep(4)
    global start_cycle_time
    start_cycle_time = datetime.now(timezone(timedelta(hours=3)))
    last_activity_time = start_cycle_time

    while True:
        # noinspection PyTypeChecker
        task_data = await redis_client.brpop('queue', timeout=5)
        if task_data:
            _, task_data = task_data
            task = Task.model_validate_json(task_data.decode('utf-8'))
            await execute_task(task, redis_client, mouse)
            last_activity_time = datetime.now(timezone(timedelta(hours=3)))
        last_activity_time = await check_timer(last_activity_time, start_cycle_time, mouse)


def run_main():
    asyncio.run(main())


if __name__ == '__main__':
    run_main()
