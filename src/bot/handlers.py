import asyncio
import logging

from aiogram import F, Router
from aiogram.types import BufferedInputFile, Message
from aiogram.exceptions import TelegramNetworkError

from controllers.telegram import get_balance_pic
from runtime import request_shutdown

router = Router()

logger = logging.getLogger(__name__)


@router.message(F.chat.id == -1003063247252, F.text == "/balance")
async def balance(message: Message):
    buffer = await get_balance_pic()
    photo_bytes = buffer.getvalue()
    last_exc: BaseException | None = None
    retry_delays = (2, 5, 10)
    for attempt in range(1, 4):
        try:
            await message.answer_photo(
                BufferedInputFile(photo_bytes, filename="balance.png"),
                disable_notification=True,
            )
            return
        except TelegramNetworkError as exc:
            last_exc = exc
            if attempt >= 3:
                break
            logger.warning(
                "Failed to send /balance photo (attempt %s/3): %s: %s",
                attempt,
                type(exc).__name__,
                exc,
            )
            await asyncio.sleep(retry_delays[attempt - 1])
        except Exception as exc:
            last_exc = exc
            logger.exception("Unexpected error while sending /balance photo")
            break

    logger.error("Failed to send /balance photo after 3 attempts: %s", last_exc)
    if last_exc is None:
        reason = "Failed to send /balance photo: no exception details"
    else:
        reason = f"Failed to send /balance photo: {type(last_exc).__name__}: {last_exc}"
    request_shutdown(reason)
