import asyncio
from datetime import timedelta, timezone, datetime
import logging.config
from pynput.mouse import Controller
import redis.asyncio as redis

from config import get_logging_config, settings
from consts import Colors, Coords, WorkspaceCoords
from controllers.actions import Actions
from controllers.requests import send_report
from controllers.window_checker import WindowChecker
from internal import Step, Task


last_restart_hour = None


async def get_next_restart_time():
    current_time = datetime.now(timezone(timedelta(hours=3)))
    next_restart_times = []
    if settings.RESTARTS_AT is not None:
        for t in settings.RESTARTS_AT:
            next_restart_times.append(current_time.replace(hour=t, minute=0, second=0, microsecond=0))
    next_restart_times = [t if t > current_time else t + timedelta(days=1) for t in next_restart_times]
    if not next_restart_times:
        return None, None

    next_restart_time = min(next_restart_times)
    time_until_restart = next_restart_time - current_time
    hours, remainder = divmod(time_until_restart.seconds, 3600)
    minutes = remainder // 60
    time_until_restart_str = f"{hours:02} hours {minutes:02} minutes."
    return time_until_restart_str


async def check_time(mouse: Controller):
    global last_restart_hour
    current_time = datetime.now(timezone(timedelta(hours=3)))
    if (
        current_time.hour in [settings.FIRST_RESTART_AT, settings.SECOND_RESTART_AT]
        and last_restart_hour != current_time.hour
    ):
        logging.info(f"Performing restarting emulator. Check '.env' file for settings.")
        await Actions.reopen_emulator(mouse)
        last_restart_hour = current_time.hour
        logging.info(
            f"Emulator started. Next restart after {await get_next_restart_time()}"
        )


async def execute_task(task: Task, redis_client: redis, mouse: Controller, attempts: int = 0):
    await asyncio.sleep(3)
    logging.info(f"Executing task id {task.order_id} for {task.requisite} with amount {task.amount}")
    await Actions.click_on_const(mouse, Coords.ANDROID_NICKNAME_SECTION, 3)
    await Actions.input_value(value=task.requisite)
    await Actions.click_on_const(mouse, Coords.ANDROID_AMOUNT_SECTION, 3)
    await Actions.input_value(value=str(task.amount).replace('.', ','))

    workspace = await Actions.take_screenshot_of_region(
        WorkspaceCoords.WORKSPACE_TOP_LEFT, WorkspaceCoords.WORKSPACE_BOTTOM_RIGHT
    )
    transfer_button = await Actions.find_color_square(
        image=workspace, color=Colors.ANDROID_GREEN, tolerance_percent=25
    )
    if transfer_button:
        await Actions.click_on_finded(mouse, transfer_button, 'TRANSFER BUTTON')
    else:
        logging.info(f"Task {task.order_id} failed. Can't find transfer button.")
    workspace = await Actions.take_screenshot_of_region(
        WorkspaceCoords.WORKSPACE_TOP_LEFT, WorkspaceCoords.WORKSPACE_BOTTOM_RIGHT
    )
    transfer_confirm_button = await Actions.find_color_square(
        image=workspace, color=Colors.ANDROID_GREEN, tolerance_percent=25
    )
    if transfer_confirm_button:
        await Actions.click_on_finded(mouse, transfer_confirm_button, 'TRANSFER CONFIRM BUTTON')
    else:
        logging.info(f"Task {task.order_id} failed. Can't find transfer confirm button.")
    transfer_confirm_section = None
    for _ in range(10):
        workspace = await Actions.take_screenshot_of_region(
            WorkspaceCoords.WORKSPACE_TOP_LEFT, WorkspaceCoords.WORKSPACE_BOTTOM_RIGHT
        )
        transfer_confirm_section = await Actions.find_color_square(
            image=workspace, color=Colors.FINAL_GREEN, tolerance_percent=10
        )
        if transfer_confirm_section:
            break
        else:
            await asyncio.sleep(0.4)
    else:
        logging.info(f"Task {task.order_id} failed. Can't find transfer confirm section.")
    task.status = 1 if transfer_confirm_section is not None else 0
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
    global last_restart_hour
    current_time = datetime.now(timezone(timedelta(hours=3)))
    last_restart_hour = current_time.hour
    restart_after = await get_next_restart_time()
    if restart_after:
        text = f"Next restart after {restart_after}"
    else:
        text = "Working without restarts."

    redis_client = redis.Redis(db=10)
    logging_config = get_logging_config('worker_android')
    logging.config.dictConfig(logging_config)

    mouse = Controller()
    if not await WindowChecker.check_window():
        await Actions.open_emulator(mouse)

    logging.info(f'Worker started. {text}')
    await asyncio.sleep(4)

    while True:
        await check_time(mouse)
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
