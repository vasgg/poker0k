import asyncio
from datetime import datetime, timedelta, timezone
import logging
from pathlib import Path
from zoneinfo import ZoneInfo

from aiohttp import BasicAuth, ClientSession
from pyautogui import hotkey, screenshot, typewrite
from pynput.mouse import Button, Controller

from internal.consts import Colors, Coords, RedisNames, WorkspaceCoords
from internal.schemas import CheckType, Task


async def restore_current_task_to_queue(task: Task, redis_client):
    serialized_task = task.model_dump_json()
    await redis_client.rpush(RedisNames.QUEUE, serialized_task)
    logging.info(f"Task {task.order_id} restored to the main queue.")


async def handle_failure_and_restart(task, redis_client, mouse):
    import worker

    await restore_current_task_to_queue(task, redis_client)
    await redis_client.sadd(RedisNames.RESTARTED_TASKS, str(task.order_id))
    logging.info("Performing restart app after failed task.")
    await Actions.reopen_pokerok_client(mouse)
    worker.last_restart_time = datetime.now(timezone(timedelta(hours=3)))


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
        logging.info(text)
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
        logging.info(text)
        if delay_after > 0:
            await asyncio.sleep(delay_after)

    @staticmethod
    async def input_value(value: str):
        await asyncio.sleep(1)
        hotkey("ctrlleft", "a")
        await asyncio.sleep(1)
        if "." in value:
            typewrite(value.split(".")[0])
            await asyncio.sleep(1)
            typewrite("\u002e")
            await asyncio.sleep(1)
            typewrite(value.split(".")[1])
        else:
            typewrite(value)
        await asyncio.sleep(1)
        logging.info(f"Input value: {value}")

    @staticmethod
    def is_color_match(pixel_color, target_color, tolerance_percent=0):
        tolerance = [tolerance_percent * 255 // 100] * 3
        return all(abs(pixel_color[i] - target_color[i]) <= tolerance[i] for i in range(3))

    @staticmethod
    async def name_or_money_error_check(check: CheckType, tolerance_percent: int = 10) -> bool:
        match check:
            case CheckType.MONEY:
                top_left = WorkspaceCoords.BALANCE_CHECK_TOP_LEFT
                bottom_right = WorkspaceCoords.BALANCE_CHECK_BOTTOM_RIGHT
            case CheckType.NAME:
                top_left = WorkspaceCoords.NAME_CHECK_TOP_LEFT
                bottom_right = WorkspaceCoords.NAME_CHECK_BOTTOM_RIGHT
            case _:
                return False
        image = await Actions.take_screenshot_of_region(top_left, bottom_right)
        pixels = image.load()
        width, height = image.size
        for x in range(width):
            for y in range(height):
                if Actions.is_color_match(pixels[x, y][:3], (227, 50, 38), tolerance_percent):
                    del image
                    return True
        del image
        return False

    @staticmethod
    async def find_square_color(
        color: tuple[int, int, int] | tuple[tuple[int, int, int], ...],
        coordinates: tuple[tuple[int, int], tuple[int, int]],
        tolerance_percent: int = 20,
        sqare_size: int = 11,
    ):
        colors: tuple[tuple[int, int, int], ...]
        if color and isinstance(color[0], int):
            colors = (color,)  # Backward compatibility: single color tuple.
        else:
            colors = color

        top_left, bottom_right = coordinates
        image = await Actions.take_screenshot_of_region(top_left, bottom_right)
        width, height = image.size
        pixels = image.load()
        half_square = sqare_size // 2

        for x in range(half_square, width - half_square):
            for y in range(half_square, height - half_square):
                matched = True
                for dx in range(-half_square, half_square + 1):
                    for dy in range(-half_square, half_square + 1):
                        if not any(
                            Actions.is_color_match(
                                pixels[x + dx, y + dy][:3],
                                one_color,
                                tolerance_percent,
                            )
                            for one_color in colors
                        ):
                            matched = False
                            break
                    if not matched:
                        break
                if matched:
                    del image
                    absolute_coords = (
                        top_left[0] + x,
                        top_left[1] + y,
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
        moscow_time = datetime.now(moscow_tz).strftime("%d.%m.%Y_%H.%M.%S")
        file = (
            f"{moscow_time}_{task.order_id}_{task.user_id}_{task.requisite}_${task.amount}_{task.status}.png"
            if not debug
            else f"{moscow_time}_{task.order_id}_DEBUG_{task.requisite}_${task.amount}_{task.status}.png"
        )
        scrnsht = screenshot()
        gray_screenshot = scrnsht.convert("L")
        path = Path("screenshots")
        gray_screenshot.save(path / file)
        logging.info(f"Screenshot saved to: {file}")
        return path / file

    @staticmethod
    async def reopen_pokerok_client(mouse: Controller):
        await Actions.click_on_const(mouse, Coords.CLOSE_APP_BUTTON, 10)
        await start_app_flow(mouse)


async def start_app_flow(mouse: Controller):
    await Actions.click_on_const(mouse, Coords.OPEN_APP_BUTTON)
    await Actions.click_on_const(mouse, Coords.OPEN_APP_BUTTON, 35)
    # await Actions.click_on_const(mouse, Coords.LOGIN_BUTTON, 35)
    # await Actions.click_on_const(mouse, Coords.CONFIRM_LOGIN_BUTTON, 35)
    # login_button = await Actions.find_square_color(
    #     color=Colors.WHITE,
    #     coordinates=(
    #         WorkspaceCoords.CONFIRM_LOGIN_BUTTON_TOP_LEFT,
    #         WorkspaceCoords.CONFIRM_LOGIN_BUTTON_TOP_TOP_RIGHT,
    #     ),
    #     sqare_size=2,
    # )
    # if login_button:
    #     await Actions.click_on_finded(mouse, login_button, "CONFIRM LOGIN BUTTON", delay_after=20)
    #
    #


    # else:
    #     await Actions.click_on_const(mouse, Coords.CONFIRM_LOGIN_BUTTON, 20)
    # login_button = await Actions.find_square_color(
    #     color=Colors.DEBUG_RUST,
    #     coordinates=(
    #         WorkspaceCoords.CONFIRM_LOGIN_BUTTON_TOP_LEFT,
    #         WorkspaceCoords.CONFIRM_LOGIN_BUTTON_TOP_TOP_RIGHT,
    #     ),
    #     sqare_size=2,
    # )
    # if login_button:
    #     await Actions.click_on_finded(mouse, login_button, "CONFIRM LOGIN BUTTON", delay_after=20)
    # else:
    #     await Actions.click_on_const(mouse, Coords.CONFIRM_LOGIN_BUTTON, 20)

    # await Actions.click_on_const(mouse, Coords.CLOSE_BANNER_BUTTON, 20)
    # await Actions.click_on_const(mouse, Coords.CLOSE_BANNER_BUTTON_2, 20)



    banner = await Actions.find_square_color(
        color=Colors.RUST,
        coordinates=(
            WorkspaceCoords.BANNER_CHECK_TOP_LEFT,
            WorkspaceCoords.BANNER_CHECK_BOTTOM_RIGHT,
        ),
        sqare_size=5,
    )
    if banner:
        await Actions.click_on_const(mouse, Coords.CLOSE_BANNER_BUTTON_2, 20)

    banner = await Actions.find_square_color(
        color=Colors.RUST,
        coordinates=(
            WorkspaceCoords.BANNER_CHECK_TOP_LEFT,
            WorkspaceCoords.BANNER_CHECK_BOTTOM_RIGHT,
        ),
        sqare_size=5,
    )
    if banner:
        await Actions.click_on_const(mouse, Coords.CLOSE_BANNER_BUTTON_2, 20)

    browser = await Actions.find_square_color(
      color=(Colors.BROWSER_LIGHT, Colors.BROWSER_DARK),
      coordinates=(WorkspaceCoords.BANNER_CHECK_TOP_LEFT, WorkspaceCoords.BANNER_CHECK_BOTTOM_RIGHT),
      sqare_size=5,
    )
    if browser:
        await Actions.click_on_const(mouse, Coords.CLOSE_BROWSER, 20)

    browser = await Actions.find_square_color(
        color=(Colors.BROWSER_LIGHT, Colors.BROWSER_DARK),
        coordinates=(WorkspaceCoords.BANNER_CHECK_TOP_LEFT, WorkspaceCoords.BANNER_CHECK_BOTTOM_RIGHT),
        sqare_size=5,
    )
    if browser:
        await Actions.click_on_const(mouse, Coords.CLOSE_BROWSER, 20)



    await Actions.click_on_const(mouse, Coords.CASHIER_BUTTON, 20)
    await Actions.click_on_const(mouse, Coords.TRANSFER_SECTION, 20)
    # await Actions.click_on_const(mouse, Coords.NICKNAME_BUTTON, 5)


async def send_update(cell: str, value: int, *, http: ClientSession, settings):
    auth = BasicAuth(
        settings.NGROK_USER.get_secret_value(),
        settings.NGROK_PASSWORD.get_secret_value(),
    )
    url = f"{settings.NGROK_URL.get_secret_value()}/gsheet/update/{cell}/{value}"
    try:
        async with http.post(url, auth=auth) as resp:
            await resp.read()
    except Exception:
        pass


async def blink(color: str, *, http: ClientSession, settings):
    auth = BasicAuth(
        settings.NGROK_USER.get_secret_value(),
        settings.NGROK_PASSWORD.get_secret_value(),
    )
    url = f"{settings.NGROK_URL.get_secret_value()}/blink/{color}"
    try:
        async with http.get(url, auth=auth) as resp:
            await resp.read()
    except Exception:
        pass
