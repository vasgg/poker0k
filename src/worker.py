import asyncio
import logging
from datetime import timedelta, timezone, datetime

from pynput.mouse import Controller
from redis import asyncio as redis

from config import settings, setup_worker, setup_bot
from controllers.actions import Actions
from controllers.executor import worker_loop

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

    global last_restart_time
    last_restart_time = datetime.now(timezone(timedelta(hours=3)))

    redis_client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        password=settings.REDIS_PASSWORD.get_secret_value(),
    )

    mouse = Controller()

    stop_event = asyncio.Event()

    polling_task = asyncio.create_task(dispatcher.start_polling(bot))
    worker_task = asyncio.create_task(worker_loop(redis_client, mouse, settings, stop_event))

    try:
        await asyncio.gather(polling_task, worker_task)
    except (asyncio.CancelledError, KeyboardInterrupt):
        logging.info("Shutdown signal received (main).")
    finally:
        logging.info("Stopping background tasks...")
        stop_event.set()
        polling_task.cancel()
        worker_task.cancel()
        await asyncio.gather(polling_task, worker_task, return_exceptions=True)
        logging.info("All tasks stopped. App shutdown complete.")


def run_main():
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Manual shutdown.")


if __name__ == "__main__":
    run_main()
