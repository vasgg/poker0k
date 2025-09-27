import asyncio
import logging
from datetime import timedelta, datetime, timezone

from aiohttp import ClientSession, ClientTimeout, TCPConnector
from pynput.mouse import Controller
from redis import asyncio as redis
import pyautogui

from config import Settings
from controllers.actions import Actions
from controllers.executor import worker_loop

last_restart_time: datetime | None = None


async def check_time(mouse: Controller, settings: Settings):
    global last_restart_time
    current_time = datetime.now(timezone(timedelta(hours=3)))
    if (current_time - last_restart_time) >= timedelta(minutes=settings.RESET_AFTER_MINS):
        logging.info("Performing scheduled restart app.")
        await Actions.reopen_pokerok_client(mouse)
        last_restart_time = current_time
        logging.info("App started.")


async def main():
    from config import settings, setup_worker, setup_bot

    global last_restart_time
    last_restart_time = datetime.now(timezone(timedelta(hours=3)))
    setup_worker("pokerok_worker")
    bot, dispatcher = setup_bot()
    pyautogui.FAILSAFE = False


    redis_client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        password=settings.REDIS_PASSWORD.get_secret_value(),
    )

    http = ClientSession(
        timeout=ClientTimeout(total=5),
        connector=TCPConnector(limit=50),
    )

    mouse = Controller()
    stop_event = asyncio.Event()

    polling_task = asyncio.create_task(dispatcher.start_polling(bot, skip_updates=True))
    worker_task = asyncio.create_task(worker_loop(redis_client, mouse, settings, stop_event, http=http))

    logging.info("Worker and polling tasks started.")

    try:
        done, pending = await asyncio.wait([polling_task, worker_task], return_when=asyncio.FIRST_COMPLETED)
        logging.info("One of the process stopped, initiating shutdown...")
        stop_event.set()
        for task in pending:
            task.cancel()
        await asyncio.gather(*pending, return_exceptions=True)
    finally:
        await http.close()

    logging.info("App shutdown completed gracefully.")


def run_main():
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Manual shutdown from console.")


if __name__ == "__main__":
    run_main()
