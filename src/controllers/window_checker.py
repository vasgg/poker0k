import logging
import pygetwindow as gw

logger = logging.getLogger(__name__)


class WindowChecker:
    @staticmethod
    async def check_window() -> bool:
        windows = gw.getAllWindows()
        for window in windows:
            print(window.title, window.width, window.left)
        #     if window.title == 'BlueStacks Player':
        #         if window.width == 428 and window.left == 1067:
        #             logger.info("Checking BlueStacks Player. Size and position: GOOD.")
        #             return True
        # logger.info(
        #     "Checking BlueStacks Player. Size and position: BAD.\n"
        #     "                                          Going to restart emulator."
        # )
        # return False
