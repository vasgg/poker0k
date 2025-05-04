import asyncio
import logging
from pyautogui import press
from pynput.mouse import Controller
from redis import asyncio as redis

from config import Settings
from controllers.actions import Actions, handle_failure_and_restart
from controllers.telegram import send_telegram_report
from internal.consts import Colors, Coords, RedisNames
from internal.schemas import CheckType, ErrorType, Step, Task
from request import send_error_report, send_report


async def execute_task(
    task: Task, redis_client: redis.Redis, mouse: Controller, settings: Settings, attempts: int = 0
):
    await asyncio.sleep(3)
    logging.info(f"Executing task id {task.order_id} for {task.requisite} with amount {task.amount}")
    nickname = "dnk-jarod" if "dev-" in task.callback_url else task.requisite
    amount = "1.11" if "dev-" in task.callback_url else str(task.amount)
    await Actions.click_on_const(mouse, Coords.CASHIER_FOCUS_SECTION)
    await Actions.click_on_const(mouse, Coords.CASHIER_FOCUS_SECTION, 3)
    press("pgup")
    check_cashier_bottom_section = await Actions.find_square_color(color=Colors.DARK_GRAY, sqare_size=20)
    if check_cashier_bottom_section:
        cashier = await Actions.take_screenshot(task=task)
        await send_telegram_report(
            f"Task {task.order_id} failed. Problem with cashier detected.",
            task=task,
            image_path=cashier,
        )
        return
    await Actions.click_on_const(mouse, Coords.NICKNAME_SECTION, 3)
    await Actions.input_value(value=nickname)
    await Actions.click_on_const(mouse, Coords.AMOUNT_SECTION, 3)
    await Actions.input_value(value=amount)
    transfer_button = await Actions.find_square_color(color=Colors.GREEN)
    if transfer_button:
        await Actions.click_on_finded(mouse, transfer_button, "TRANSFER BUTTON", delay_after=5)
    else:
        logging.info(f"Task {task.order_id} failed. Can't find transfer button.")
        await handle_failure_and_restart(task, redis_client, mouse)
        return
    if await Actions.name_or_money_error_check(check=CheckType.NAME):
        logging.info(f"Task {task.order_id} failed. Incorrect name.")
        await send_error_report(task, ErrorType.INCORRECT_NAME, settings)
        name_image_path = await Actions.take_screenshot(task=task)
        await send_telegram_report(
            f"Task {task.order_id} failed. Incorrect name.",
            task=task,
            image_path=name_image_path,
        )
        return
    if await Actions.name_or_money_error_check(check=CheckType.MONEY):
        logging.info(f"Task {task.order_id} failed. Insufficient funds.")
        await send_error_report(task, ErrorType.INSUFFICIENT_FUNDS, settings)
        funds_image_path = await Actions.take_screenshot(task=task)
        await send_telegram_report(
            f"Task {task.order_id} failed. Insufficient funds.",
            task=task,
            image_path=funds_image_path,
        )
        return
    transfer_confirm_button = await Actions.find_square_color(color=Colors.GREEN, confirm_button=True)
    if transfer_confirm_button:
        await Actions.click_on_finded(mouse, transfer_confirm_button, "TRANSFER CONFIRM BUTTON")
    else:
        logging.info(f"Task {task.order_id} failed. Can't find transfer confirm button.")
        await handle_failure_and_restart(task, redis_client, mouse)
        return
        # button_image_path = await Actions.take_screenshot(task=task)
        # await send_telegram_report(
        #     f"Task {task.order_id} failed. Can't find transfer confirm button.",
        #     task=task,
        #     image_path=button_image_path,
        # )
        # return
    transfer_confirm_section = None
    for _ in range(10):
        transfer_confirm_section = await Actions.find_square_color(color=Colors.FINAL_GREEN)
        if transfer_confirm_section:
            break
        else:
            await asyncio.sleep(0.4)
    else:
        logging.info(f"Task {task.order_id} failed. Can't find transfer confirm section.")
        confirm_section_image_path = await Actions.take_screenshot(task=task)
        await send_telegram_report(
            f"Task {task.order_id} failed. Can't find transfer confirm section.",
            task=task,
            image_path=confirm_section_image_path,
        )

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


async def worker_loop(redis_client, mouse, settings, stop_event: asyncio.Event):
    from worker import check_time

    await asyncio.sleep(4)

    try:
        while not stop_event.is_set():
            await check_time(mouse)

            try:
                task_data = await asyncio.wait_for(redis_client.brpop(RedisNames.QUEUE), timeout=1)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                logging.info("Worker loop cancelled during Redis waiting.")
                break

            if task_data:
                _, task_data = task_data
                task = Task.model_validate_json(task_data.decode("utf-8"))
                set_name = RedisNames.DEV_SET if "dev-" in task.callback_url else RedisNames.PROD_SET
                is_in_completed = await redis_client.sismember(set_name, str(task.order_id))
                if not is_in_completed and task.status not in [1, 2]:
                    await execute_task(task, redis_client, mouse, settings)
                else:
                    logging.info(f"Task {task.order_id} skipped — already processed...")
    except asyncio.CancelledError:
        logging.info("Worker loop cancelled explicitly.")
    finally:
        logging.info("Worker loop stopped gracefully.")
