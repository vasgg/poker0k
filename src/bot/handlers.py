from io import BytesIO

from aiogram import F, Router
from aiogram.types import BufferedInputFile, Message

from controllers.actions import Actions
from internal.consts import WorkspaceCoords

router = Router()


@router.message(F.chat.id == -4655514577, F.text == "/balance")
async def balance(message: Message):
    picture = await Actions.take_screenshot_of_region(
        WorkspaceCoords.BALANCE_WINDOW_TOP_LEFT, WorkspaceCoords.BALANCE_WINDOW_BOTTOM_RIGHT
    )
    buffer = BytesIO()
    picture.save(buffer, format='PNG')
    buffer.seek(0)

    await message.answer_photo(
        BufferedInputFile(buffer.read(), filename='balance.png'),
        disable_notification=True
    )
