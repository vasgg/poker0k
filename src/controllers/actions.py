import asyncio
from datetime import datetime
import logging
from pathlib import Path
from zoneinfo import ZoneInfo

from pyautogui import typewrite, screenshot
from pynput.mouse import Button, Controller

from consts import Coords
from internal import Task

logger = logging.getLogger(__name__)


class Actions:
    @staticmethod
    async def click_transfer_section():
        mouse = Controller()
        mouse.position = Coords.TRANSFER_SECTION
        mouse.click(Button.left)
        logger.info("Transfer section clicked...")
        logger.info("Awaiting 4 seconds...")
        await asyncio.sleep(4)

    @staticmethod
    async def click_close_cashier_button():
        mouse = Controller()
        mouse.position = Coords.CLOSE_CASHIER_BUTTON
        mouse.click(Button.left)
        logger.info("Close cashier button clicked...")
        logger.info("Awaiting 4 seconds...")
        await asyncio.sleep(4)

    @staticmethod
    async def click_nickname_section():
        mouse = Controller()
        mouse.position = Coords.NICKNAME_SECTION
        mouse.click(Button.left)
        logger.info("Nickname section clicked...")
        logger.info("Awaiting 3 seconds...")
        await asyncio.sleep(3)

    @staticmethod
    async def enter_nickname(requisite: str):
        typewrite(requisite)
        logger.info(f'Enter nickname: {requisite}...')
        logger.info("Awaiting 3 seconds...")
        await asyncio.sleep(3)

    @staticmethod
    async def click_amount_section():
        mouse = Controller()
        mouse.position = Coords.AMOUNT_SECTION
        mouse.click(Button.left)
        logger.info("Click to amount section...")
        logger.info("Awaiting 3 seconds...")
        await asyncio.sleep(3)

    @staticmethod
    async def enter_amount(amount: str):
        typewrite(amount)
        logger.info(f'Enter amount: {amount}...')
        logger.info("Awaiting 3 seconds...")
        await asyncio.sleep(3)

    @staticmethod
    async def tab_clicking():
        mouse = Controller()
        mouse.position = Coords.NEXT_SECTION_BUTTON
        mouse.click(Button.left)
        await asyncio.sleep(3)
        mouse.position = Coords.HOME_SECTION_BUTTON
        mouse.click(Button.left)
        logger.info("Tab clicking performed...")
        logger.info("Awaiting 3 seconds...")
        await asyncio.sleep(3)

    @staticmethod
    async def click_transfer_button():
        mouse = Controller()
        mouse.position = Coords.TRANSFER_BUTTON
        mouse.click(Button.left)
        logger.info("Click transfer button...")
        logger.info("Awaiting 4 seconds...")
        await asyncio.sleep(4)

    @staticmethod
    async def click_transfer_confirm_button():
        mouse = Controller()
        mouse.position = Coords.TRANSFER_CONFIRM_BUTTON
        mouse.click(Button.left)
        await asyncio.sleep(0.1)
        logger.info("Transfer confirm button clicked...")
        logger.info("Awaiting 3 seconds...")
        await asyncio.sleep(3)

    @staticmethod
    async def take_screenshot(task: Task, debug: bool = False):
        moscow_tz = ZoneInfo("Europe/Moscow")
        moscow_time = datetime.now(moscow_tz).strftime('%d.%m.%Y_%H.%M.%S')
        file = (
            f'{moscow_time}_{task.order_id}_{task.user_id}_{task.requisite}_${task.amount}_{task.status}.png'
            if not debug
            else f'debug_{task.requisite}_${task.amount}_{task.status}.png'
        )
        scrnsht = screenshot()
        gray_screenshot = scrnsht.convert('L')
        path = Path('screenshots')
        gray_screenshot.save(path / file)
        logger.info(f"Screenshot {file} saved...")
        logger.info("Awaiting 3 seconds...")
        await asyncio.sleep(3)
