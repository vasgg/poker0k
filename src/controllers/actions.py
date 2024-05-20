import asyncio
from datetime import datetime
import logging
from zoneinfo import ZoneInfo

import pyautogui

from consts import Coords
from enums import Status, Task

logger = logging.getLogger(__name__)


class Actions:
    @staticmethod
    async def click_transfer_section():
        pyautogui.click(Coords.TRANSFER_SECTION)
        logger.info("Transfer section clicked...")
        logger.info("Awaiting 10 seconds...")
        await asyncio.sleep(3)

    @staticmethod
    async def click_nickname_section():
        pyautogui.click(Coords.NICKNAME_SECTION)
        logger.info("Nickname section clicked...")
        logger.info("Awaiting 3 seconds...")
        await asyncio.sleep(3)

    @staticmethod
    async def enter_nickname(nick: str):
        pyautogui.typewrite(nick)
        logger.info(f'Enter nickname: {nick}...')
        logger.info("Awaiting 5 seconds...")
        await asyncio.sleep(5)

    @staticmethod
    async def click_amount_section():
        pyautogui.click(Coords.AMOUNT_SECTION)
        logger.info("Amount section clicked...")
        logger.info("Awaiting 3 seconds...")
        await asyncio.sleep(3)

    @staticmethod
    async def enter_amount(amount: str):
        pyautogui.typewrite(amount)
        logger.info(f'Enter amount: {amount}...')
        logger.info("Awaiting 3 seconds...")
        await asyncio.sleep(3)

    @staticmethod
    async def click_transfer_button():
        pyautogui.click(Coords.TRANSFER_BUTTON)
        pyautogui.click(Coords.TRANSFER_BUTTON)
        logger.info("Transfer button clicked...")
        logger.info("Awaiting 3 seconds...")
        await asyncio.sleep(3)

    @staticmethod
    async def click_transfer_confirm_button():
        pyautogui.click(Coords.TRANSFER_CONFIRM_BUTTON)
        logger.info("Transfer confirm button clicked...")
        logger.info("Awaiting 2 seconds...")
        await asyncio.sleep(2)

    @staticmethod
    async def take_screenshot(task: Task, status: Status):
        moscow_tz = ZoneInfo("Europe/Moscow")
        moscow_time = datetime.now(moscow_tz).strftime('%d.%m.%Y|%H:%M:%S')
        file_name = f'{moscow_time}|{task.order_id}|{task.user_id}|{task.requisite}|${task.amount}|{status.value}.png'
        screenshot = pyautogui.screenshot()
        gray_screenshot = screenshot.convert('L')
        gray_screenshot.save(f'screenshots/{file_name}')
        logger.info(f"Screenshot {file_name} saved...")
        logger.info("Awaiting 3 seconds...")
        await asyncio.sleep(3)
