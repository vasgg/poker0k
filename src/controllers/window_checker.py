import asyncio
import logging

import pyautogui

from consts import (CASHIER_BUTTON, CLOSE_AD_BUTTON, CONFIRM_LOGIN_BUTTON, CONFIRM_TRANSFER_SECTION, GRAY, GREEN, LIGHT_GREEN, LOGIN_BUTTON,
                    RED, RESTART_BUTTON, RUST,
                    TRANSFER_BUTTON, TRANSFER_CONFIRM_BUTTON, TRANSFER_TAB, WHITE)

logger = logging.getLogger(__name__)


class WindowChecker:
    @staticmethod
    async def check_logout():
        check_logout = pyautogui.pixelMatchesColor(*RESTART_BUTTON, GREEN, tolerance=10)
        if check_logout:
            pyautogui.click(RESTART_BUTTON)
            logger.info("Disconnected. Restart button clicked...")
        else:
            logger.info("Connected, continue...")

    @staticmethod
    async def check_ad():
        check_ad = pyautogui.pixelMatchesColor(*CLOSE_AD_BUTTON, GRAY, tolerance=20)
        if check_ad:
            pyautogui.click(CLOSE_AD_BUTTON)
            await asyncio.sleep(1)
            pyautogui.click(CLOSE_AD_BUTTON)
            logger.info("Ad closed...")
        else:
            logger.info("No ad, continue...")

    @staticmethod
    async def check_login():
        check_login = pyautogui.pixelMatchesColor(*LOGIN_BUTTON, RUST, tolerance=20)
        if check_login:
            pyautogui.click(LOGIN_BUTTON)
            logger.info("Disconnected. Login button clicked...")
            await asyncio.sleep(3)
        else:
            logger.info("Connected, continue...")

    @staticmethod
    async def check_confirm_login():
        check_confirm_login = pyautogui.pixelMatchesColor(*CONFIRM_LOGIN_BUTTON, RUST, tolerance=20)
        if check_confirm_login:
            pyautogui.click(CONFIRM_LOGIN_BUTTON)
            logger.info("Disconnected. Confirm login button clicked...")
            logger.info("Connection in progress. Awaiting 10 seconds...")
            await asyncio.sleep(10)
        else:
            logger.info("Connected, continue...")

    @staticmethod
    async def check_cashier():
        check_cashier = pyautogui.pixelMatchesColor(*CASHIER_BUTTON, WHITE, tolerance=20)
        if check_cashier:
            pyautogui.click(CASHIER_BUTTON)
            logger.info("Cashier button clicked...")
            logger.info("Loading in progress. Awaiting 10 seconds...")
            await asyncio.sleep(10)
        logger.info("Connected, continue...")

    @staticmethod
    async def check_transfer_section():
        check_transfer_section = pyautogui.pixelMatchesColor(*TRANSFER_TAB, RED, tolerance=25)
        if check_transfer_section:
            logger.info("We are in the transfer section. Going short path...")
            return True
        logger.info("We are not in the transfer section. Going long path...")
        return False

    @staticmethod
    async def check_transfer_button():
        check_transfer_button = pyautogui.pixelMatchesColor(*TRANSFER_BUTTON, GREEN, tolerance=20)
        if check_transfer_button:
            logger.info("Transfer button detected...")
            return True
        logger.info("Transfer button not detected...")
        return False

    @staticmethod
    async def check_transfer_confirm_button():
        check_transfer_confirm_button = pyautogui.pixelMatchesColor(*TRANSFER_CONFIRM_BUTTON, GREEN, tolerance=20)
        if check_transfer_confirm_button:
            logger.info("Transfer confirm button detected...")
            return True
        logger.info("Transfer confirm button not detected...")
        return False

    @staticmethod
    async def check_confirm_transfer_section(nickname: str = 'Mein Herz Brent', amount: str = '1'):
        check_transfer_section = pyautogui.pixelMatchesColor(*CONFIRM_TRANSFER_SECTION, LIGHT_GREEN, tolerance=20)
        if check_transfer_section:
            logger.info(f'Transfer to: {nickname}, amount: ${amount}, status: successful...')
            return True
        logger.info(f'Transfer to: {nickname}, amount: ${amount}, status: failed...')
        return False
