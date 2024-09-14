import asyncio
from datetime import datetime
import logging
from pathlib import Path
from zoneinfo import ZoneInfo

from pyautogui import hotkey, screenshot, typewrite
from pynput.mouse import Button, Controller

from consts import Colors, Coords, WorkspaceCoords
from controllers.window_checker import WindowChecker
from internal import Task

logger = logging.getLogger(__name__)


class Actions:
    @staticmethod
    async def click_on_const(mouse: Controller, coords: Coords, delay_after: int = 0, delay_before: int = 0):
        text = f"Mouse clicked: {coords.name.replace('_', ' ')}." if delay_after == 0 else f"Mouse clicked: {coords.name.replace('_', ' ')}. Waiting {delay_after} seconds."
        if delay_before > 0:
            # logger.info(f"Waiting {delay_before} seconds before clicking {coords.name.replace('_', ' ')}...")
            await asyncio.sleep(delay_before)
        mouse.position = coords.value
        mouse.click(Button.left)
        logger.info(f"Mouse clicked: {coords.name.replace('_', ' ')}.")
        if delay_after > 0:
            logger.info(f"Waiting {delay_after} seconds after clicking {coords.name.replace('_', ' ')}.")
            await asyncio.sleep(delay_after)

    @staticmethod
    async def click_on_finded(mouse: Controller, pixel: tuple[int, int], label: str, delay_after: int = 3):
        mouse.position = pixel
        mouse.click(Button.left)
        logger.info(f"Mouse clicked on finded button: {label}.")
        if delay_after > 0:
            logger.info(f"Waiting {delay_after} seconds after clicking {label}.")
            await asyncio.sleep(delay_after)

    @staticmethod
    async def input_value(value: str):
        hotkey('ctrlleft', 'a')
        typewrite(value)
        logger.info(f'Input value: {value}.')

    @staticmethod
    def is_color_match(pixel, color, tolerance_percent):
        return all(abs(pixel[i] - color[i]) / color[i] <= tolerance_percent / 100 for i in range(3) if color[i] != 0)

    @staticmethod
    async def find_color_square(image, color=(0, 128, 0), tolerance_percent=0) -> tuple[int, int] | None:
        size = 11
        width, height = image.size
        pixels = image.load()

        half_square = size // 2

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
                    absolute_coords = (WorkspaceCoords.WORKSPACE_TOP_LEFT[0] + x,
                                       WorkspaceCoords.WORKSPACE_TOP_LEFT[1] + y)
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
            else f'{moscow_time}_{task.order_id}_DEBUG_{task.requisite}_${task.amount}_{task.status}.png'
        )
        scrnsht = screenshot()
        gray_screenshot = scrnsht.convert('L')
        path = Path('screenshots')
        gray_screenshot.save(path / file)
        logger.info(f"File {file} saved. Awaiting 3 seconds.")
        await asyncio.sleep(3)


async def reopen_emulator(mouse: Controller):
    logger.info(f"Starting reopen emulator process.")
    await Actions.click_on_const(mouse, Coords.ANDROID_CLOSE_EMULATOR_BUTTON, 3)
    workspace = await Actions.take_screenshot_of_region(
        WorkspaceCoords.WORKSPACE_TOP_LEFT, WorkspaceCoords.WORKSPACE_BOTTOM_RIGHT
    )
    transfer_button = await Actions.find_color_square(
        image=workspace, color=Colors.ANDROID_CLOSE_BUTTON_COLOR, tolerance_percent=20
    )
    if transfer_button:
        await Actions.click_on_finded(mouse, transfer_button, 'CONFIRM EXIT BUTTON')
    else:
        logging.info("Error. Can't find CONFIRM EXIT BUTTON")
        return
    await Actions.click_on_const(mouse, Coords.ANDROID_OPEN_EMULATOR_BUTTON)
    await Actions.click_on_const(mouse, Coords.ANDROID_OPEN_EMULATOR_BUTTON, 180)
    await Actions.click_on_const(mouse, Coords.ANDROID_DONT_SHOW_TODAY, 5)
    await Actions.click_on_const(mouse, Coords.ANDROID_ME_SECTION, 10)
    await Actions.click_on_const(mouse, Coords.ANDROID_CASHIER_BUTTON, 10)
    await Actions.click_on_const(mouse, Coords.ANDROID_CASHIER_SETTINGS, 10)
    await Actions.click_on_const(mouse, Coords.ANDROID_TRANSFER_SECTION, 10)


async def reopen_cashier(mouse: Controller):
    close_button = await WindowChecker.check_pixel_and_click(
        Coords.ANDROID_CLOSE_CASHIER_BUTTON, Colors.GRAY.value, mouse
    )
    if close_button:
        workspace = await Actions.take_screenshot_of_region(
            WorkspaceCoords.CASHIER_BUTTON_TOP_LEFT, WorkspaceCoords.CASHIER_BUTTON_BOTTOM_RIGHT
        )
        cashier_button = await Actions.find_color_square(
            image=workspace, color=Colors.RUST, tolerance_percent=20
        )
        if cashier_button:
            await Actions.click_on_finded(mouse, cashier_button, 'CASHIER BUTTON', 10)
