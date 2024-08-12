import asyncio
import logging
from pyautogui import pixelMatchesColor
from pynput.mouse import Button, Controller

from consts import Colors, Coords

logger = logging.getLogger(__name__)


class WindowChecker:
    @staticmethod
    async def check_logout() -> None:
        check_logout = pixelMatchesColor(*Coords.RESTART_BUTTON, Colors.LIGHT_GREEN, tolerance=25)
        if check_logout:
            mouse = Controller()
            mouse.position = Coords.RESTART_BUTTON
            mouse.click(Button.left)
            await asyncio.sleep(1)
            logger.info("Disconnected. Restart button clicked...")
            logger.info("Connection in progress. Awaiting 10 seconds...")
            await asyncio.sleep(10)
        else:
            logger.info("Connected, continue...")

    @staticmethod
    async def check_ad() -> None:
        check_ad = pixelMatchesColor(*Coords.CLOSE_AD_BUTTON, Colors.GRAY, tolerance=35)
        if check_ad:
            mouse = Controller()
            mouse.position = Coords.CLOSE_AD_BUTTON
            mouse.click(Button.left)
            await asyncio.sleep(0.1)
            logger.info("Ad closed...")
        else:
            logger.info("No ad, continue...")

    @staticmethod
    async def check_login() -> None:
        check_login = pixelMatchesColor(*Coords.LOGIN_BUTTON, Colors.RUST, tolerance=35)
        if check_login:
            mouse = Controller()
            mouse.position = Coords.LOGIN_BUTTON
            mouse.click(Button.left)
            await asyncio.sleep(0.1)
            logger.info("Disconnected. Login button clicked...")
            logger.info("Connection in progress. Awaiting 5 seconds...")
            await asyncio.sleep(5)
        else:
            logger.info("Connected, continue...")

    @staticmethod
    async def check_confirm_login():
        check_confirm_login = pixelMatchesColor(*Coords.CONFIRM_LOGIN_BUTTON, Colors.RUST, tolerance=20)
        if check_confirm_login:
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
        check_cashier = pixelMatchesColor(*Coords.CASHIER_BUTTON, Colors.WHITE, tolerance=25)
        if check_cashier:
            mouse = Controller()
            mouse.position = Coords.CASHIER_BUTTON
            mouse.click(Button.left)
            logger.info("Cashier button clicked...")
            logger.info("Loading in progress. Awaiting 8 seconds...")
            await asyncio.sleep(8)
            return
        logger.info("Cashier button not found...")

    @staticmethod
    async def check_transfer_section():
        check_transfer_section = pixelMatchesColor(*Coords.TRANSFER_SECTION, Colors.RED, tolerance=25)
        if check_transfer_section:
            logger.info("We are in the transfer section...")
            return True
        logger.info("We are not in the transfer section. Check cashier window and transfer section...")
        return False

    @staticmethod
    async def check_transfer_button():
        check_light_transfer_button = pixelMatchesColor(*Coords.TRANSFER_BUTTON, Colors.LIGHT_GREEN, tolerance=65)
        check_dark_transfer_button = pixelMatchesColor(*Coords.TRANSFER_BUTTON, Colors.DARK_GREEN, tolerance=65)
        if check_light_transfer_button or check_dark_transfer_button:
            logger.info("Transfer button detected...")
            return True
        logger.info("Transfer button not detected...")
        return False

    @staticmethod
    async def check_transfer_confirm_button():
        check_light_transfer_confirm_button = pixelMatchesColor(
            *Coords.ANDROID_TRANSFER_CONFIRM_BUTTON, Colors.LIGHT_GREEN, tolerance=65
        )
        check_dark_transfer_confirm_button = pixelMatchesColor(
            *Coords.ANDROID_TRANSFER_CONFIRM_BUTTON, Colors.DARK_GREEN, tolerance=65
        )
        if check_light_transfer_confirm_button or check_dark_transfer_confirm_button:
            logger.info("Transfer confirm button detected...")
            return True
        logger.info("Transfer confirm button not detected...")
        return False

    @staticmethod
    async def check_confirm_transfer_section():
        check_transfer_section = pixelMatchesColor(*Coords.ANDROID_CONFIRM_TRANSFER_SECTION, Colors.FINAL_GREEN, tolerance=20)
        if check_transfer_section:
            logger.info("Confirm transfer section detected...")
            return True
        logger.info("Confirm transfer section not detected...")
        return False

    @staticmethod
    async def check_close_cashier_button():
        check_close_cashier_button = pixelMatchesColor(*Coords.CLOSE_CASHIER_BUTTON, Colors.GRAY, tolerance=50)
        if check_close_cashier_button:
            mouse = Controller()
            mouse.position = Coords.CLOSE_CASHIER_BUTTON
            mouse.click(Button.left)
            await asyncio.sleep(0.1)
            logger.info("Close Cashier button clicked...")
            return True
        logger.info("Cashier not closed after timeout...")
        return False

    @staticmethod
    async def check_cashier_fullscreen_button():
        check_cashier_fullscreen_button = pixelMatchesColor(
            *Coords.CASHIER_FULLSCREEN_BUTTON, Colors.MENU_RED, tolerance=25
        )
        if check_cashier_fullscreen_button:
            mouse = Controller()
            mouse.position = Coords.CASHIER_FULLSCREEN_BUTTON
            mouse.click(Button.left)
            await asyncio.sleep(1)
            logger.info("Cashier fullscreen toggled...")
            return True
        logger.info("Something went wrong...")
        return False

    @staticmethod
    async def check_me_section_android():
        check_me_section_android = pixelMatchesColor(*Coords.ANDROID_ME_SECTION, Colors.ANDROID_RED, tolerance=25)
        if check_me_section_android:
            logger.info("Me section detected...")
            return True
        logger.info("Me section not detected...")
        return False
