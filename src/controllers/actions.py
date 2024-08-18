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
    WORKSPACE_TOP_LEFT = 1270, 290
    WORKSPACE_BOTTOM_RIGHT = 1385, 750

    @staticmethod
    async def mouse_click_on_const(mouse: Controller, coords: Coords, delay_after: int = 0, delay_before: int = 0):
        if delay_before > 0:
            logger.info(f"Waiting {delay_before} seconds before clicking {coords.name.replace('_', ' ')}...")
            await asyncio.sleep(delay_before)
        mouse.position = coords.value
        mouse.click(Button.left)
        logger.info(f"Mouse clicked: {coords.name}...")
        if delay_after > 0:
            logger.info(f"Waiting {delay_after} seconds after clicking {coords.name.replace('_', ' ')}...")
            await asyncio.sleep(delay_after)

    @staticmethod
    async def mouse_click_on_finded(mouse: Controller, pixel: tuple[int, int], label: str):
        mouse.position = pixel
        mouse.click(Button.left)
        logger.info(f"Mouse clicked on finded button: {label}...")

    @staticmethod
    async def enter_nickname(requisite: str):
        typewrite(requisite)
        logger.info(f'Enter nickname: {requisite}...')
        logger.info("Awaiting 3 seconds...")
        await asyncio.sleep(3)

    @staticmethod
    async def enter_amount(amount: str):
        typewrite(amount)
        logger.info(f'Enter amount: {amount}...')
        logger.info("Awaiting 3 seconds...")
        await asyncio.sleep(3)

    @staticmethod
    def is_color_match(pixel, color, tolerance_percent):
        return all(abs(pixel[i] - color[i]) / color[i] <= tolerance_percent / 100 for i in range(3) if color[i] != 0)

    @staticmethod
    async def find_color_square(image, color=(0, 128, 0), square_size=11, tolerance_percent=0) -> tuple[int, int] | None:
        width, height = image.size
        pixels = image.load()

        half_square = square_size // 2

        for x in range(half_square, width - half_square):
            for y in range(half_square, height - half_square):
                matched = True
                for dx in range(-half_square, half_square + 1):
                    for dy in range(-half_square, half_square + 1):
                        if not Actions.is_color_match(pixels[x + dx, y + dy][:3], color, tolerance_percent):
                            matched = False
                            break
                    if not matched:
                        break
                if matched:
                    del image
                    absolute_coords = Actions.WORKSPACE_TOP_LEFT[0] + x, Actions.WORKSPACE_BOTTOM_RIGHT[1] + y
                    return absolute_coords
        del image
        return None

    @staticmethod
    async def take_screenshot_of_region(top_left: tuple, bottom_right: tuple):
        x1, y1 = top_left
        x2, y2 = bottom_right
        width = x2 - x1
        height = y2 - y1
        region = (x1, y1, width, height)
        scrnsht = screenshot(region=region)
        return scrnsht

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
