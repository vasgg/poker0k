from aiogram import F, Router
from aiogram.types import BufferedInputFile, Message

from controllers.telegram import get_balance_pic

router = Router()


@router.message(F.chat.id == -4655514577, F.text == "/balance")
async def balance(message: Message):
    buffer = await get_balance_pic()
    await message.answer_photo(BufferedInputFile(buffer.read(), filename="balance.png"), disable_notification=True)
