
import redis.asyncio as redis
import asyncio
import logging.config

from config import get_logging_config
from controllers.actions import Actions
from controllers.window_checker import WindowChecker
from enums import Status, Task


async def execute_task(task: Task):
    logging.info(f"Executing task for {task.nickname} with amount {task.amount}")
    if await WindowChecker.check_transfer_section():
        await Actions.click_nickname_section()
        await Actions.enter_nickname(nick=task.nickname)
        await Actions.click_amount_section()
        await Actions.enter_amount(amount=str(task.amount))
        if await WindowChecker.check_transfer_button():
            await Actions.click_transfer_button()
        if await WindowChecker.check_transfer_confirm_button():
            await Actions.click_transfer_confirm_button()
        if await WindowChecker.check_confirm_transfer_section():
            await Actions.take_screenshot(Status.SUCCESS, nick=task.nickname, amount=str(task.amount))
            logging.info(f"Completed task for {task.nickname} with amount {task.amount}")
        else:
            await Actions.take_screenshot(Status.FAIL, nick=task.nickname, amount=str(task.amount))
            logging.info(f"Something went wrong with task for {task.nickname} with amount {task.amount}")

    else:
        await WindowChecker.check_login()
        await WindowChecker.check_confirm_login()
        await WindowChecker.check_ad()
        await WindowChecker.check_cashier()

        await Actions.click_transfer_section()
        await Actions.click_nickname_section()
        await Actions.enter_nickname(nick=task.nickname)
        await Actions.click_amount_section()
        await Actions.enter_amount(amount=str(task.amount))

        if await WindowChecker.check_transfer_button():
            await Actions.click_transfer_button()
        if await WindowChecker.check_transfer_confirm_button():
            await Actions.click_transfer_confirm_button()
        if await WindowChecker.check_confirm_transfer_section():
            await Actions.take_screenshot(Status.SUCCESS, nick=task.nickname, amount=str(task.amount))
            logging.info(f"Completed task for {task.nickname} with amount {task.amount}")
        else:
            await Actions.take_screenshot(Status.FAIL, nick=task.nickname, amount=str(task.amount))
            logging.info(f"Something went wrong with task for {task.nickname} with amount {task.amount}")


async def main():
    redis_client = redis.Redis(db=10)
    pubsub = redis_client.pubsub()
    await pubsub.subscribe('tasks')

    logging_config = get_logging_config('worker')
    logging.config.dictConfig(logging_config)
    logging.info("Subscribed to 'tasks' channel. Waiting for tasks...")
    async for message in pubsub.listen():
        if message['type'] == 'message':
            task_data = message['data'].decode('utf-8')
            task = Task.parse_raw(task_data)
            await execute_task(task)


if __name__ == "__main__":
    asyncio.run(main())
