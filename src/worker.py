import asyncio
import logging

from aiohttp import ClientSession, ClientTimeout, TCPConnector
import socket
from pynput.mouse import Controller
from redis import asyncio as redis
import pyautogui

from config import Settings
from controllers.actions import Actions
from controllers.executor import worker_loop
from runtime import get_minutes_until_next_restart, get_worker_now, set_last_restart_time, set_shutdown_event


async def check_time(mouse: Controller, settings: Settings):
    if get_minutes_until_next_restart(settings.RESET_AFTER_MINS, now=get_worker_now()) == 0:
        logging.info("Performing scheduled restart app.")
        await Actions.reopen_pokerok_client(mouse)
        set_last_restart_time()
        logging.info("App started.")


def update_last_restart_time():
    set_last_restart_time()


async def main():
    from config import settings, setup_worker, setup_bot

    set_last_restart_time()
    setup_worker("pokerok_worker")
    bot, dispatcher = setup_bot()
    pyautogui.FAILSAFE = False

    try:
        async with (
            redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD.get_secret_value(),
            ) as redis_client,
            ClientSession(
                timeout=ClientTimeout(total=5),
                connector=TCPConnector(limit=50, family=socket.AF_INET),
            ) as http,
        ):
            mouse = Controller()
            stop_event = asyncio.Event()
            set_shutdown_event(stop_event)

            polling_task = asyncio.create_task(dispatcher.start_polling(bot, skip_updates=True))
            worker_task = asyncio.create_task(worker_loop(redis_client, mouse, settings, stop_event, http=http))
            tasks = [polling_task, worker_task]

            logging.info("Worker and polling tasks started.")

            try:
                await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                logging.info("One of the process stopped, initiating shutdown...")
            finally:
                stop_event.set()
                for task in tasks:
                    task.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)
    finally:
        await bot.session.close()

    logging.info("App shutdown completed gracefully.")


def run_main():
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Manual shutdown from console.")


if __name__ == "__main__":
    run_main()
