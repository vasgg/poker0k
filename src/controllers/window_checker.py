import logging
import pygetwindow as gw

logger = logging.getLogger(__name__)


class WindowChecker:
    @staticmethod
    async def check_window() -> bool:
        windows = gw.getAllWindows()
        for window in windows:
            if window.title == 'BlueStacks App Player':
                if window.width == 428 and window.left == 1067:
                    logger.info("Check BlueStacks App Player size and position: GOOD.")
                    return True
        logger.info("Check BlueStacks App Player size and position: BAD.\n"
                    " " * 43 + "Going to restart emulator.")
        return False
