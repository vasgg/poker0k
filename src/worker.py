import asyncio
from datetime import timedelta, timezone, datetime
import logging.config
from pathlib import Path

from pynput.mouse import Controller
import redis.asyncio as redis
from atexit import register

from config import get_logging_config, settings
from consts import Colors, Coords
from controllers.actions import Actions
from request import send_error_report, send_report
from controllers.telegram import send_report_at_exit, send_telegram_report

from internal import CheckType, ErrorType, Step, Task


last_restart_time: datetime | None = None


async def check_time(mouse: Controller):
    global last_restart_time
    current_time = datetime.now(timezone(timedelta(hours=3)))
    if (current_time - last_restart_time) >= timedelta(minutes=50):
        logging.info("Performing scheduled restart app.")
        await Actions.reopen_pokerok_client(mouse)
        last_restart_time = current_time
        logging.info("App started.")


async def restore_tasks(task: Task, redis_client):
    serialized_task = task.model_dump_json()
    await redis_client.rpush("FER_queue", serialized_task)
    logging.info(f"Task {task.order_id} restored to the main queue.")


async def execute_task(task: Task, redis_client: redis, mouse: Controller, attempts: int = 0):
    await asyncio.sleep(3)
    logging.info(f"Executing task id {task.order_id} for {task.requisite} with amount {task.amount}")
    nickname = 'dnk-jarod' if 'dev-' in task.callback_url else task.requisite
    amount = '5111.11' if 'dev-' in task.callback_url else str(task.amount)
    await Actions.click_on_const(mouse, Coords.NICKNAME_SECTION, 3)
    await Actions.input_value(value=nickname)
    await Actions.click_on_const(mouse, Coords.AMOUNT_SECTION, 3)
    await Actions.input_value(value=amount)
    # await Actions.click_on_const(mouse, Coords.TRANSFER_BUTTON, 3)
    transfer_button = await Actions.find_square_color(color=Colors.GREEN)
    if transfer_button:
        await Actions.click_on_finded(mouse, transfer_button, 'TRANSFER BUTTON')
    else:
        logging.info(f"Task {task.order_id} failed. Can't find transfer button.")
        await send_telegram_report(
            f"Task {task.order_id} failed. Can't find transfer button.",
            task=task,
        )
        return
    if await Actions.name_or_money_error_check(check=CheckType.NAME):
        logging.info(f"Task {task.order_id} failed. Incorrect name.")
        # await redis_client.sadd('incorrect_names', str(task.requisite))
        await send_error_report(task, ErrorType.INCORRECT_NAME)
        await send_telegram_report(
            f"Task {task.order_id} failed. Incorrect name.",
            task=task,
        )
        return
    if await Actions.name_or_money_error_check(check=CheckType.MONEY):
        logging.info(f"Task {task.order_id} failed. Insufficient funds.")
        await send_error_report(task, ErrorType.INSUFFICIENT_FUNDS)
        await send_telegram_report(
            f"Task {task.order_id} failed. Insufficient funds.",
            task=task,
        )
        return
    # await Actions.click_on_const(mouse, Coords.TRANSFER_CONFIRM_BUTTON, 5)
    transfer_confirm_button = await Actions.find_square_color(color=Colors.GREEN)
    if transfer_confirm_button:
        await Actions.click_on_finded(mouse, transfer_confirm_button, 'TRANSFER CONFIRM BUTTON')
    else:
        logging.info(f"Task {task.order_id} failed. Can't find transfer confirm button.")
        await send_telegram_report(
            f"Task {task.order_id} failed. Can't find transfer confirm button.",
            task=task,
        )
    transfer_confirm_section = None
    for _ in range(10):
        # workspace = await Actions.take_screenshot_of_region(
        #     WorkspaceCoords.WORKSPACE_TOP_LEFT, WorkspaceCoords.WORKSPACE_BOTTOM_RIGHT
        # )
        # transfer_confirm_section = await Actions.find_color_square(
        #     image=workspace, color=Colors.FINAL_GREEN, tolerance_percent=10
        # )
        transfer_confirm_section = await Actions.find_square_color(color=Colors.FINAL_GREEN)
        if transfer_confirm_section:
            break
        else:
            await asyncio.sleep(0.4)
    else:
        logging.info(f"Task {task.order_id} failed. Can't find transfer confirm section.")
        await send_telegram_report(f"Task {task.order_id} failed. Can't find transfer confirm section.", task=task)

    task.status = 1 if transfer_confirm_section is not None else 0
    logging.info(f"Task {task.order_id} status: {task.status}")
    set_name_completed = "dev_completed_tasks" if "dev-" in task.callback_url else "prod_completed_tasks"

    if task.status == 1:
        task.step = Step.PROCESSED

        await redis_client.lpush("FER_reports", task.model_dump_json())
        await redis_client.sadd(set_name_completed, str(task.order_id))

        await send_report(task=task, redis_client=redis_client)
        await Actions.take_screenshot(task=task)
    else:
        task.step = Step.FAILED
        await redis_client.lpush("FER_reports", task.model_dump_json())
        attempts += 1
        await Actions.take_screenshot(task=task, debug=True)
        logging.info(f"Task {task.order_id} failed. Can't find transfer confirm section.")
        if attempts < settings.MAX_ATTEMPTS:
            await execute_task(task=task, redis_client=redis_client, mouse=mouse, attempts=attempts)
        else:
            image_path = await Actions.take_screenshot(task=task)
            await send_telegram_report(
                f"Task {task.order_id} failed after {attempts} attempts, check the app.",
                task=task,
                image_path=image_path,
            )
            logging.info(f"Task {task.order_id} failed after {attempts} attempts.")
            await send_report(
                task=task,
                redis_client=redis_client,
                problem=f"Transfer to {task.requisite} with amount {task.amount} failed. Please check the app.",
            )
            # logging.info("Restoring task to the main queue.")
            # await restore_tasks(task, redis_client)
            # logging.info(f"Performing restarting emulator after failed task.")
            # await Actions.reopen_pokerok(mouse)


async def main():
    register(send_report_at_exit)

    logs_directory = Path("logs")
    screenshots_directory = Path("screenshots")
    logs_directory.mkdir(parents=True, exist_ok=True)
    screenshots_directory.mkdir(parents=True, exist_ok=True)

    global last_restart_time
    current_time = datetime.now(timezone(timedelta(hours=3)))
    last_restart_time = current_time

    redis_client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        password=settings.REDIS_PASSWORD.get_secret_value(),
    )
    logging_config = get_logging_config("worker_pip")
    logging.config.dictConfig(logging_config)

    mouse = Controller()
    await send_telegram_report(
        message="Worker started.",
        disable_notification=True
    )

    logging.info("Worker started.")
    await asyncio.sleep(4)

    while True:
        await check_time(mouse)
        task_data = await redis_client.brpop("FER_queue", timeout=5)

        if task_data:
            _, task_data = task_data
            task = Task.model_validate_json(task_data.decode("utf-8"))
            set_name = "dev_completed_tasks" if "dev-" in task.callback_url else "prod_completed_tasks"
            is_in_completed = await redis_client.sismember(set_name, str(task.order_id))
            # is_in_bad_names = await redis_client.sismember("incorrect_names", task.requisite)
            if not is_in_completed:
                # if not is_in_bad_names:
                if task.status not in [1, 2]:  # все статусы, кроме complete & cancel.
                    await execute_task(task, redis_client, mouse)
                # else:
                #     logging.info(f"Task {task.order_id} skipped — incorrect name...")
            else:
                logging.info(f"Task {task.order_id} skipped — already processed...")


def run_main():
    asyncio.run(main())


if __name__ == "__main__":
    run_main()
