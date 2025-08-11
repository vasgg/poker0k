import asyncio
import logging

from aiohttp import ClientSession
from pyautogui import press
from pynput.mouse import Controller
from redis import asyncio as redis

from config import Settings
from controllers.actions import Actions, blink, send_update
from controllers.telegram import get_balance_pic, send_telegram_report
from internal.consts import Colors, Coords, RedisNames, WorkspaceCoords
from internal.schemas import CheckType, Stage, Step, Task
from request import send_report


async def execute_task(
    task: Task, redis_client: redis.Redis, mouse: Controller, settings: Settings, http: ClientSession
):
    await asyncio.sleep(3)
    logging.info(f"Executing task id {task.order_id} for {task.requisite} with amount {task.amount}")
    nickname = "dnk-jarod" if "dev-" in task.callback_url else task.requisite
    amount = "1.11" if "dev-" in task.callback_url else str(task.amount)
    await Actions.click_on_const(mouse, Coords.CASHIER_FOCUS_SECTION)
    await Actions.click_on_const(mouse, Coords.CASHIER_FOCUS_SECTION, 3)
    press("pgup")
    check_cashier_bottom_section = await Actions.find_square_color(
        color=Colors.DARK_GRAY,
        coordinates=(
            WorkspaceCoords.CASHIER_BOTTOM_TOP_LEFT,
            WorkspaceCoords.CASHIER_BOTTOM_TOP_RIGHT,
        ),
        sqare_size=20
    )
    if check_cashier_bottom_section:
        cashier = await Actions.take_screenshot(task=task)
        await send_telegram_report(
            "Task failed. Problem with cashier detected.",
            task=task,
            image=cashier,
            chats=(settings.TG_REPORTS_CHAT, settings.TG_BOT_ADMIN_ID),
        )
        return
    # await Actions.click_on_const(mouse, Coords.TRANSFER_SECTION, 3)
    # await Actions.click_on_const(mouse, Coords.NICKNAME_BUTTON, 3)
    await Actions.click_on_const(mouse, Coords.NICKNAME_SECTION, 3)
    await Actions.input_value(value=nickname)
    await Actions.click_on_const(mouse, Coords.AMOUNT_SECTION, 3)
    await Actions.input_value(value=amount)
    if await Actions.name_or_money_error_check(check=CheckType.MONEY):
        logging.info(f"Task {task.order_id} failed. Insufficient funds.")
        # await send_error_report(task, ErrorType.INSUFFICIENT_FUNDS, settings)
        funds_image_path = await Actions.take_screenshot(task=task)
        await send_telegram_report(
            "Task failed. Insufficient funds.",
            task=task,
            image=funds_image_path,
            chats=(settings.TG_REPORTS_CHAT, settings.TG_BOT_ADMIN_ID),
        )
        return
    transfer_button = await Actions.find_square_color(
        color=Colors.GREEN,
        coordinates=(
            WorkspaceCoords.WORKSPACE_TOP_LEFT,
            WorkspaceCoords.WORKSPACE_BOTTOM_RIGHT,
        ),
        sqare_size=5
    )
    if transfer_button:
        await Actions.click_on_finded(mouse, transfer_button, "TRANSFER BUTTON", delay_after=5)
    else:
        logging.info(f"Task {task.order_id} failed. Can't find transfer button.")
        screenshot = await Actions.take_screenshot(task=task)
        await send_telegram_report(
            "Task failed. Can't find transfer button.",
            task=task,
            image=screenshot,
            chats=(settings.TG_REPORTS_CHAT, settings.TG_BOT_ADMIN_ID),
        )

        # is_already_restarted = await redis_client.sismember(RedisNames.RESTARTED_TASKS, str(task.order_id))
        # if is_already_restarted:
        #     logging.info(f"Task {task.order_id} skipped — already restarted...")
        #     screenshot = await Actions.take_screenshot(task=task)
        #     await send_telegram_report(
        #         f"Task {task.order_id} failed after restart PokerokClient. Can't find transfer button.",
        #         task=task,
        #         image_path=screenshot,
        #     )
        #     return
        # await handle_failure_and_restart(task, redis_client, mouse)
        return
    if await Actions.name_or_money_error_check(check=CheckType.NAME):
        logging.info(f"Task {task.order_id} failed. Incorrect name.")
        # await send_error_report(task, ErrorType.INCORRECT_NAME, settings)
        name_image_path = await Actions.take_screenshot(task=task)
        await send_telegram_report(
            "Task failed. Incorrect name.",
            task=task,
            image=name_image_path,
            chats=(settings.TG_REPORTS_CHAT, settings.TG_BOT_ADMIN_ID),
        )
        await blink("red", http=http, settings=settings)
        return

    transfer_confirm_button = await Actions.find_square_color(
        color=Colors.GREEN,
        coordinates=(
            WorkspaceCoords.CONFIRM_BUTTON_TOP_LEFT,
            WorkspaceCoords.CONFIRM_BUTTON_BOTTOM_RIGHT,
        ),
    )
    if transfer_confirm_button:
        await Actions.click_on_finded(mouse, transfer_confirm_button, "TRANSFER CONFIRM BUTTON")
    else:
        logging.info(f"Task {task.order_id} failed. Can't find transfer confirm button.")
        screenshot = await Actions.take_screenshot(task=task)
        await send_telegram_report(
            "Task failed. Can't find transfer confirm button.",
            task=task,
            image=screenshot,
            chats=(settings.TG_REPORTS_CHAT, settings.TG_BOT_ADMIN_ID),
        )
        # is_already_restarted = await redis_client.sismember(RedisNames.RESTARTED_TASKS, str(task.order_id))
        # if is_already_restarted:
        #     logging.info(f"Task {task.order_id} skipped — already restarted...")
        #     screenshot = await Actions.take_screenshot(task=task)
        #     await send_telegram_report(
        #         f"Task {task.order_id} failed after restart PokerokClient. Can't find transfer confirm button.",
        #         task=task,
        #         image_path=screenshot,
        #     )
        #     return
        # await handle_failure_and_restart(task, redis_client, mouse)
        return
        # button_image_path = await Actions.take_screenshot(task=task)
        # await send_telegram_report(
        #     f"Task {task.order_id} failed. Can't find transfer confirm button.",
        #     task=task,
        #     image_path=button_image_path,
        # )
        # return
    transfer_confirm_section = await Actions.find_square_color(
        color=Colors.FINAL_GREEN,
        coordinates=(
            WorkspaceCoords.TRANSFER_CONFIRM_TOP_LEFT,
            WorkspaceCoords.TRANSFER_CONFIRM_BOTTOM_RIGHT,
        )
    )
    if transfer_confirm_section:
        await Actions.click_on_finded(mouse, transfer_confirm_section, "TRANSFER SUCCESSFUL BUTTON")
        await Actions.click_on_const(mouse, Coords.NICKNAME_BUTTON, 3)

    else:
        logging.info(f"Task {task.order_id} failed. Can't find transfer confirm section.")
        confirm_section_image_path = await Actions.take_screenshot(task=task)
        await send_telegram_report(
            "Task failed. Can't find transfer confirm section.",
            task=task,
            image=confirm_section_image_path,
            chats=(settings.TG_REPORTS_CHAT, settings.TG_BOT_ADMIN_ID),
        )

    task.status = 1 if transfer_confirm_section is not None else 0
    logging.info(f"Task {task.order_id} status: {task.status}")
    set_name_completed = "dev_completed_tasks" if "dev-" in task.callback_url else "prod_completed_tasks"

    if task.status == 1:
        task.step = Step.PROCESSED

        await redis_client.lpush("FER_reports", task.model_dump_json())
        await redis_client.sadd(set_name_completed, str(task.order_id))

        await send_report(task=task, redis_client=redis_client, settings=settings)
        # await Actions.take_screenshot(task=task)
        balance_pic = await get_balance_pic()
        await send_telegram_report(
            "Task completed.",
            task=task,
            image=balance_pic,
            chats=(settings.TG_REPORTS_CHAT,),
            disable_notification=True,
        )
        await blink("yellow", http=http, settings=settings)
    else:
        # task.step = Step.FAILED
        # await redis_client.lpush("FER_reports", task.model_dump_json())
        # attempts += 1
        # await Actions.take_screenshot(task=task, debug=True)
        image_path = await Actions.take_screenshot(task=task)
        await send_telegram_report(
            "Task failed.",
            task=task,
            image=image_path,
            chats=(settings.TG_REPORTS_CHAT, settings.TG_BOT_ADMIN_ID),
        )
        await blink("red", http=http, settings=settings)
        logging.info(f"Task {task.order_id} failed.")


async def worker_loop(redis_client, mouse, settings, stop_event, *, http: ClientSession):
    from worker import check_time

    await asyncio.sleep(4)
    try:
        while not stop_event.is_set():
            await check_time(mouse, settings)

            try:
                task_data = await asyncio.wait_for(redis_client.brpop(RedisNames.QUEUE), timeout=1)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                logging.info("Worker loop cancelled during Redis waiting.")
                break

            if not task_data:
                continue

            _, task_data = task_data
            task = Task.model_validate_json(task_data.decode("utf-8"))

            set_name = RedisNames.DEV_SET if "dev-" in task.callback_url else RedisNames.PROD_SET
            is_in_completed = await redis_client.sismember(set_name, str(task.order_id))
            is_existing_user = await redis_client.sismember(RedisNames.REQUISITES, str(task.requisite))

            if not is_existing_user and settings.STAGE == Stage.PROD:
                await redis_client.sadd(RedisNames.REQUISITES, str(task.requisite))
                set_length = await redis_client.scard(RedisNames.REQUISITES)
                await blink("blue", http=http, settings=settings)
                await send_update("C5", set_length, http=http, settings=settings)

            if not is_in_completed and task.status not in [1, 2]:
                await execute_task(task, redis_client, mouse, settings, http=http)
            else:
                logging.info(f"Task {task.order_id} skipped — already processed...")
    except asyncio.CancelledError:
        logging.info("Worker loop cancelled explicitly.")
    finally:
        logging.info("Worker loop stopped gracefully.")
