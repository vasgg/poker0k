import asyncio
from datetime import datetime
import logging
from zoneinfo import ZoneInfo

import pyautogui

from consts import AMOUNT_SECTION, NICKNAME_SECTION, TRANSFER_BUTTON, TRANSFER_CONFIRM_BUTTON, TRANSFER_SECTION
from enums import Status

logger = logging.getLogger(__name__)


class Actions:
    @staticmethod
    async def click_transfer_section():
        pyautogui.click(TRANSFER_SECTION)
        logger.info("Transfer section clicked...")
        logger.info("Awaiting 10 seconds...")
        await asyncio.sleep(3)

    @staticmethod
    async def click_nickname_section():
        pyautogui.click(NICKNAME_SECTION)
        logger.info("Nickname section clicked...")
        logger.info("Awaiting 3 seconds...")
        await asyncio.sleep(3)

    @staticmethod
    async def enter_nickname(nick: str = 'Mein Herz Brent'):
        pyautogui.typewrite(nick)
        logger.info(f'Enter email: {nick}...')
        logger.info("Awaiting 5 seconds...")
        await asyncio.sleep(5)

    @staticmethod
    async def click_amount_section():
        pyautogui.click(AMOUNT_SECTION)
        logger.info("Amount section clicked...")
        logger.info("Awaiting 3 seconds...")
        await asyncio.sleep(3)

    @staticmethod
    async def enter_amount(amount: str = '1'):
        pyautogui.typewrite(amount)
        logger.info(f'Enter amount: {amount}...')
        logger.info("Awaiting 3 seconds...")
        await asyncio.sleep(3)

    @staticmethod
    async def click_transfer_button():
        pyautogui.click(TRANSFER_BUTTON)
        pyautogui.click(TRANSFER_BUTTON)
        logger.info("Transfer button clicked...")
        logger.info("Awaiting 3 seconds...")
        await asyncio.sleep(3)

    @staticmethod
    async def click_transfer_confirm_button():
        pyautogui.click(TRANSFER_CONFIRM_BUTTON)
        logger.info("Transfer confirm button clicked...")
        logger.info("Awaiting 2 seconds...")
        await asyncio.sleep(2)

    @staticmethod
    async def take_screenshot(status: Status, nick: str = 'Mein Herz Brent', amount: str = '1'):
        moscow_tz = ZoneInfo("Europe/Moscow")
        moscow_time = datetime.now(moscow_tz).strftime('%d.%m.%Y|%H:%M:%S')
        file_name = f'{moscow_time}|{nick}|{amount}$|{status}.png'
        screenshot = pyautogui.screenshot()
        gray_screenshot = screenshot.convert('L')
        gray_screenshot.save(f'screenshots/{file_name}')
        logger.info(f"Screenshot {file_name} saved...")
        logger.info("Awaiting 3 seconds...")
        await asyncio.sleep(3)
