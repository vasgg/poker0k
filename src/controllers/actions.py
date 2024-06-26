import asyncio
import logging
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pyautogui
from consts import Coords
from internal import Task

logger = logging.getLogger(__name__)
pyautogui.FAILSAFE = False


class Actions:
    @staticmethod
    async def click_transfer_section():
        pyautogui.click(Coords.TRANSFER_SECTION)
        logger.info("Transfer section clicked...")
        logger.info("Awaiting 4 seconds...")
        await asyncio.sleep(4)

    @staticmethod
    async def click_close_cashier_button():
        pyautogui.click(Coords.CLOSE_CASHIER_BUTTON)
        logger.info("Transfer section clicked...")
        logger.info("Awaiting 4 seconds...")
        await asyncio.sleep(4)

    @staticmethod
    async def click_nickname_section():
        pyautogui.click(Coords.NICKNAME_SECTION)
        logger.info("Nickname section clicked...")
        logger.info("Awaiting 3 seconds...")
        await asyncio.sleep(3)

    @staticmethod
    async def enter_nickname(requisite: str):
        pyautogui.typewrite(requisite)
        logger.info(f'Enter nickname: {requisite}...')
        logger.info("Awaiting 3 seconds...")
        await asyncio.sleep(3)

    @staticmethod
    async def click_amount_section():
        pyautogui.keyDown('tab')
        pyautogui.keyUp('tab')
        pyautogui.keyDown('tab')
        pyautogui.keyUp('tab')
        # pyautogui.click(Coords.AMOUNT_SECTION)
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
    async def tab_clicking():
        pyautogui.click(Coords.NEXT_SECTION_BUTTON)
        await asyncio.sleep(3)
        pyautogui.click(Coords.HOME_SECTION_BUTTON)
        logger.info("Awaiting 3 seconds...")
        await asyncio.sleep(3)

    @staticmethod
    async def click_transfer_button():
        pyautogui.click(Coords.TRANSFER_BUTTON)
        logger.info("Transfer button clicked...")
        logger.info("Awaiting 4 seconds...")
        await asyncio.sleep(4)

    @staticmethod
    async def click_transfer_confirm_button():
        pyautogui.click(Coords.TRANSFER_CONFIRM_BUTTON)
        await asyncio.sleep(0.1)
        pyautogui.click(Coords.TRANSFER_CONFIRM_BUTTON)
        logger.info("Transfer confirm button clicked...")
        logger.info("Awaiting 3 seconds...")
        await asyncio.sleep(3)

    @staticmethod
    async def take_screenshot(task: Task):
        moscow_tz = ZoneInfo("Europe/Moscow")
        moscow_time = datetime.now(moscow_tz).strftime('%d.%m.%Y_%H.%M.%S')
        file = f'{moscow_time}_{task.order_id}_{task.user_id}_{task.requisite}_${task.amount}_{task.status}.png'
        screenshot = pyautogui.screenshot()
        gray_screenshot = screenshot.convert('L')
        path = Path('screenshots')
        gray_screenshot.save(path / file)
        logger.info(f"Screenshot {file} saved...")
        logger.info("Awaiting 3 seconds...")
        await asyncio.sleep(3)
