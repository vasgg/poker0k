import logging
import pygetwindow as gw

logger = logging.getLogger(__name__)


class WindowChecker:
    @staticmethod
    async def check_window() -> bool:
        windows = gw.getAllWindows()
        for window in windows:
            if window.title == 'ПокерОК':
                if window.width == 1200 and window.left == 717:
                    logger.info("Checking PokerOK app. Size and position: GOOD.")
                    return True
        logger.info(
            "Checking PokerOK app. Size and position: BAD.\n"
            "                                          Going to restart app."
        )
        return False
