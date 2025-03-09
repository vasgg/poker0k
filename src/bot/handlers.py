from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from controllers.actions import Actions
from internal.consts import WorkspaceCoords

router = Router()


@router.message(Command("balance"), F.chat_id == -4655514577)
async def balance(message: Message):
    picture = await Actions.take_screenshot_of_region(
        WorkspaceCoords.BALANCE_WINDOW_TOP_LEFT, WorkspaceCoords.BALANCE_WINDOW_BOTTOM_RIGHT
    )
    await message.answer_photo(picture, disable_notification=True)
