import asyncio
from datetime import datetime
import logging
from pathlib import Path
from zoneinfo import ZoneInfo

from pyautogui import hotkey, screenshot, typewrite
from pynput.mouse import Button, Controller

from consts import Colors, Coords, WorkspaceCoords
from controllers.window_checker import WindowChecker
from internal import Size, Task

logger = logging.getLogger(__name__)


class Actions:
    @staticmethod
    async def click_on_const(mouse: Controller, coords: Coords, delay_after: int = 0, delay_before: int = 0):
        text = (
            f"Mouse clicked: {coords.name.replace('_', ' ')}."
            if delay_after == 0
            else f"Waiting {delay_after} seconds after clicking {coords.name.replace('_', ' ')}."
        )
        if delay_before > 0:
            await asyncio.sleep(delay_before)
        mouse.position = coords.value
        mouse.click(Button.left)
        logger.info(text)
        if delay_after > 0:
            await asyncio.sleep(delay_after)

    @staticmethod
    async def click_on_finded(mouse: Controller, pixel: tuple[int, int], label: str, delay_after: int = 3):
        text = (
            f"Mouse clicked on finded button: {label}."
            if delay_after == 0
            else f"Waiting {delay_after} seconds after clicking {label}."
        )
        mouse.position = pixel
        mouse.click(Button.left)
        logger.info(text)
        if delay_after > 0:
            await asyncio.sleep(delay_after)

    @staticmethod
    async def input_value(value: str):
        await asyncio.sleep(1)
        hotkey('ctrlleft', 'a')
        await asyncio.sleep(1)
        typewrite(value)
        await asyncio.sleep(1)
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
                    absolute_coords = (
                        WorkspaceCoords.WORKSPACE_TOP_LEFT[0] + x,
                        WorkspaceCoords.WORKSPACE_TOP_LEFT[1] + y,
                    )
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
    async def take_screenshot(task: Task, debug: bool = False) -> Path:
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
        logger.info(f"Screenshot successfully saved to:\n                                          {file}")
        await asyncio.sleep(3)
        return path / file

    @staticmethod
    async def reopen_emulator(mouse: Controller, size: Size = Size.SMALL, attempts: int = 1):
        logger.info(f"Starting reopen emulator process. Attempt number {attempts}.")
        if attempts > 3:
            logger.info("Emulator failed after 3 restarts. Check BlueStacks App Player.")
            return
        coords = (
            Coords.CLOSE_EMULATOR_BUTTON if size == Size.SMALL else Coords.CLOSE_EMULATOR_BUTTON_BIG
        )
        await Actions.click_on_const(mouse, coords, 3)
        workspace = await Actions.take_screenshot_of_region(
            WorkspaceCoords.WORKSPACE_TOP_LEFT, WorkspaceCoords.WORKSPACE_BOTTOM_RIGHT
        )
        exit_button = await Actions.find_color_square(
            image=workspace, color=Colors.CLOSE_BUTTON_COLOR, tolerance_percent=20
        )
        if exit_button:
            await Actions.click_on_finded(mouse, exit_button, 'CONFIRM EXIT BUTTON')
        else:
            logging.info("Error. Can't find CONFIRM EXIT BUTTON")
            return
        await start_emulator_flow(mouse, attempts + 1)

    @staticmethod
    async def open_emulator(mouse: Controller, attempts: int = 1):
        logger.info(f"Starting open emulator process. Attempt number: {attempts}.")
        await start_emulator_flow(mouse, attempts)
        logger.info(f"Emulator successfully started.")


async def start_emulator_flow(mouse: Controller, attempts: int = 1):
    await Actions.click_on_const(mouse, Coords.OPEN_EMULATOR_BUTTON)
    await Actions.click_on_const(mouse, Coords.OPEN_EMULATOR_BUTTON, 120)
    if not await WindowChecker.check_window():
        await Actions.reopen_emulator(mouse, size=Size.BIG, attempts=attempts + 1)
        return
    await Actions.click_on_const(mouse, Coords.DONT_SHOW_TODAY, 5)
    await Actions.click_on_const(mouse, Coords.ME_SECTION, 10)
    await Actions.click_on_const(mouse, Coords.CASHIER_BUTTON, 20)
    await Actions.click_on_const(mouse, Coords.CASHIER_SETTINGS, 5)
    await Actions.click_on_const(mouse, Coords.TRANSFER_SECTION, 10)
