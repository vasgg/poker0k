import asyncio
import logging

import pyautogui
from pynput.mouse import Button, Controller

from consts import Colors, Coords

logger = logging.getLogger(__name__)


class WindowChecker:
    @staticmethod
    async def check_logout() -> None:
        check_logout = pyautogui.pixelMatchesColor(*Coords.RESTART_BUTTON, Colors.LIGHT_GREEN, tolerance=25)
        if check_logout:
            # pyautogui.click(Coords.RESTART_BUTTON)
            mouse = Controller()
            mouse.position = Coords.RESTART_BUTTON
            mouse.click(Button.left)
            await asyncio.sleep(1)
            logger.info("Disconnected. Restart button clicked...")
            logger.info("Connection in progress. Awaiting 15 seconds...")
            await asyncio.sleep(15)
        else:
            logger.info("Connected, continue...")

    @staticmethod
    async def check_ad() -> None:
        check_ad = pyautogui.pixelMatchesColor(*Coords.CLOSE_AD_BUTTON, Colors.GRAY, tolerance=35)
        if check_ad:
            # pyautogui.click(Coords.CLOSE_AD_BUTTON)
            mouse = Controller()
            mouse.position = Coords.CLOSE_AD_BUTTON
            mouse.click(Button.left)
            await asyncio.sleep(0.1)
            logger.info("Ad closed...")
        else:
            logger.info("No ad, continue...")

    @staticmethod
    async def check_login() -> None:
        check_login = pyautogui.pixelMatchesColor(*Coords.LOGIN_BUTTON, Colors.RUST, tolerance=35)
        if check_login:
            # pyautogui.click(Coords.LOGIN_BUTTON)
            mouse = Controller()
            mouse.position = Coords.LOGIN_BUTTON
            mouse.click(Button.left)
            await asyncio.sleep(0.1)
            logger.info("Disconnected. Login button clicked...")
            logger.info("Connection in progress. Awaiting 20 seconds...")
            await asyncio.sleep(20)
        else:
            logger.info("Connected, continue...")

    @staticmethod
    async def check_confirm_login():
        check_confirm_login = pyautogui.pixelMatchesColor(*Coords.CONFIRM_LOGIN_BUTTON, Colors.RUST, tolerance=20)
        if check_confirm_login:
            # pyautogui.click(Coords.CONFIRM_LOGIN_BUTTON)
            mouse = Controller()
            mouse.position = Coords.CONFIRM_LOGIN_BUTTON
            mouse.click(Button.left)
            await asyncio.sleep(1)
            logger.info("Disconnected. Confirm login button clicked...")
            logger.info("Connection in progress. Awaiting 15 seconds...")
            await asyncio.sleep(15)
        else:
            logger.info("Connected, continue...")

    @staticmethod
    async def check_cashier() -> None:
        check_cashier = pyautogui.pixelMatchesColor(*Coords.CASHIER_BUTTON, Colors.WHITE, tolerance=25)
        if check_cashier:
            # pyautogui.click(Coords.CASHIER_BUTTON)
            mouse = Controller()
            mouse.position = Coords.CASHIER_BUTTON
            mouse.click(Button.left)
            logger.info("Cashier button clicked...")
            logger.info("Loading in progress. Awaiting 15 seconds...")
            await asyncio.sleep(15)
        logger.info("Cashier button not found...")

    @staticmethod
    async def check_transfer_section():
        check_transfer_section = pyautogui.pixelMatchesColor(*Coords.TRANSFER_SECTION, Colors.RED, tolerance=25)
        if check_transfer_section:
            logger.info("We are in the transfer section. Going short path...")
            return True
        logger.info("We are not in the transfer section. Check cashier window and transfer section...")
        return False

    @staticmethod
    async def check_transfer_button():
        check_light_transfer_button = pyautogui.pixelMatchesColor(
            *Coords.TRANSFER_BUTTON, Colors.LIGHT_GREEN, tolerance=65
        )
        check_dark_transfer_button = pyautogui.pixelMatchesColor(
            *Coords.TRANSFER_BUTTON, Colors.DARK_GREEN, tolerance=65
        )
        if check_light_transfer_button or check_dark_transfer_button:
            logger.info("Transfer button detected...")
            return True
        logger.info("Transfer button not detected...")
        return False

    @staticmethod
    async def check_transfer_confirm_button():
        check_light_transfer_confirm_button = pyautogui.pixelMatchesColor(
            *Coords.TRANSFER_CONFIRM_BUTTON, Colors.LIGHT_GREEN, tolerance=65
        )
        check_dark_transfer_confirm_button = pyautogui.pixelMatchesColor(
            *Coords.TRANSFER_CONFIRM_BUTTON, Colors.DARK_GREEN, tolerance=65
        )
        if check_light_transfer_confirm_button or check_dark_transfer_confirm_button:
            logger.info("Transfer confirm button detected...")
            return True
        logger.info("Transfer confirm button not detected...")
        return False

    @staticmethod
    async def check_confirm_transfer_section():
        check_transfer_section = pyautogui.pixelMatchesColor(
            *Coords.CONFIRM_TRANSFER_SECTION, Colors.FINAL_GREEN, tolerance=20
        )
        if check_transfer_section:
            logger.info("Confirm transfer section detected...")
            return True
        logger.info("Confirm transfer section not detected...")
        return False

    @staticmethod
    async def check_close_cashier_button():
        check_close_cashier_button = pyautogui.pixelMatchesColor(
            *Coords.CLOSE_CASHIER_BUTTON, Colors.GRAY, tolerance=50
        )
        if check_close_cashier_button:
            mouse = Controller()
            mouse.position = Coords.CLOSE_CASHIER_BUTTON
            mouse.click(Button.left)
            await asyncio.sleep(0.1)
            # pyautogui.click(Coords.CLOSE_CASHIER_BUTTON)
            logger.info("Close Cashier button clicked...")
            return True
        logger.info("Cashier not closed after timeout...")
        return False

    @staticmethod
    async def check_cashier_fullscreen_button():
        check_cashier_fullscreen_button = pyautogui.pixelMatchesColor(
            *Coords.CASHIER_FULLSCREEN_BUTTON, Colors.MENU_RED, tolerance=25
        )
        if check_cashier_fullscreen_button:
            await asyncio.sleep(5)
            mouse = Controller()
            mouse.position = Coords.CASHIER_FULLSCREEN_BUTTON
            mouse.click(Button.left)
            # pyautogui.click(Coords.CASHIER_FULLSCREEN_BUTTON)
            logger.info("Cashier fullscreen toggled...")
            return True
        logger.info("Cashier not closed...")
        return False
