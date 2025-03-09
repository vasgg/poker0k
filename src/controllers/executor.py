import asyncio
import logging

from pynput.mouse import Controller
from redis import asyncio as redis

from config import Settings
from controllers.actions import Actions
from controllers.telegram import send_telegram_report
from internal.consts import Colors, Coords
from internal.schemas import CheckType, ErrorType, Step, Task
from request import send_error_report, send_report


async def restore_tasks(task: Task, redis_client):
    serialized_task = task.model_dump_json()
    await redis_client.rpush("FER_queue", serialized_task)
    logging.info(f"Task {task.order_id} restored to the main queue.")


async def execute_task(task: Task, redis_client: redis, mouse: Controller, settings: Settings, attempts: int = 0):
    await asyncio.sleep(3)
    logging.info(f"Executing task id {task.order_id} for {task.requisite} with amount {task.amount}")
    nickname = "dnk-jarod" if "dev-" in task.callback_url else task.requisite
    amount = "1.11" if "dev-" in task.callback_url else str(task.amount)
    await Actions.click_on_const(mouse, Coords.NICKNAME_SECTION, 3)
    await Actions.input_value(value=nickname)
    await Actions.click_on_const(mouse, Coords.AMOUNT_SECTION, 3)
    await Actions.input_value(value=amount)
    # await Actions.click_on_const(mouse, Coords.TRANSFER_BUTTON, 3)
    transfer_button = await Actions.find_square_color(color=Colors.GREEN)
    if transfer_button:
        await Actions.click_on_finded(mouse, transfer_button, "TRANSFER BUTTON")
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
        await send_error_report(task, ErrorType.INCORRECT_NAME, settings)
        await send_telegram_report(
            f"Task {task.order_id} failed. Incorrect name.",
            task=task,
        )
        return
    if await Actions.name_or_money_error_check(check=CheckType.MONEY):
        logging.info(f"Task {task.order_id} failed. Insufficient funds.")
        await send_error_report(task, ErrorType.INSUFFICIENT_FUNDS, settings)
        await send_telegram_report(
            f"Task {task.order_id} failed. Insufficient funds.",
            task=task,
        )
        return
    # await Actions.click_on_const(mouse, Coords.TRANSFER_CONFIRM_BUTTON, 5)
    transfer_confirm_button = await Actions.find_square_color(color=Colors.GREEN)
    if transfer_confirm_button:
        await Actions.click_on_finded(mouse, transfer_confirm_button, "TRANSFER CONFIRM BUTTON")
    else:
        logging.info(f"Task {task.order_id} failed. Can't find transfer confirm button.")
        await send_telegram_report(
            f"Task {task.order_id} failed. Can't find transfer confirm button.",
            task=task,
        )
    transfer_confirm_section = None
    for _ in range(10):
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

        await send_report(task=task, redis_client=redis_client, settings=settings)
        await Actions.take_screenshot(task=task)
    else:
        task.step = Step.FAILED
        await redis_client.lpush("FER_reports", task.model_dump_json())
        attempts += 1
        await Actions.take_screenshot(task=task, debug=True)
        logging.info(f"Task {task.order_id} failed. Can't find transfer confirm section.")
        if attempts < settings.MAX_ATTEMPTS:
            await execute_task(task=task, redis_client=redis_client, mouse=mouse, attempts=attempts, settings=settings)
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
                settings=settings,
            )
            # logging.info("Restoring task to the main queue.")
            # await restore_tasks(task, redis_client)
            # logging.info(f"Performing restarting emulator after failed task.")
            # await Actions.reopen_pokerok(mouse)
