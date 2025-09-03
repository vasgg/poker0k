from aiogram import F, Router
from aiogram.types import BufferedInputFile, Message

from config import settings
from controllers.telegram import get_balance_pic

router = Router()


@router.message(F.chat.id == int(settings.TG_REPORTS_CHAT), F.text == "/balance")
async def balance(message: Message):
    buffer = await get_balance_pic()
    await message.answer_photo(BufferedInputFile(buffer.read(), filename="balance.png"), disable_notification=True)
