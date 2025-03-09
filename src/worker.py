import asyncio
from datetime import timedelta, timezone, datetime
import logging
from pynput.mouse import Controller
import redis.asyncio as redis

from config import settings, setup_worker, setup_bot
from controllers.executor import execute_task
from controllers.actions import Actions
from internal.schemas import Task


last_restart_time: datetime | None = None


async def check_time(mouse: Controller):
    global last_restart_time
    current_time = datetime.now(timezone(timedelta(hours=3)))
    if (current_time - last_restart_time) >= timedelta(minutes=50):
        logging.info("Performing scheduled restart app.")
        await Actions.reopen_pokerok_client(mouse)
        last_restart_time = current_time
        logging.info("App started.")


async def main():
    setup_worker("pokerok_worker")
    bot, dispatcher = setup_bot()
    await dispatcher.start_polling(bot)

    global last_restart_time
    current_time = datetime.now(timezone(timedelta(hours=3)))
    last_restart_time = current_time

    redis_client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        password=settings.REDIS_PASSWORD.get_secret_value(),
    )

    mouse = Controller()

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
            if not is_in_completed:
                if task.status not in [1, 2]:  # все статусы, кроме complete & cancel.
                    await execute_task(task, redis_client, mouse, settings)
            else:
                logging.info(f"Task {task.order_id} skipped — already processed...")


def run_main():
    asyncio.run(main())


if __name__ == "__main__":
    run_main()
