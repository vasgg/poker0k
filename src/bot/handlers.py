from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from config import settings
from controllers.actions import Actions
from internal.consts import WorkspaceCoords

router = Router()


@router.message(Command("balance"), F.chat_id == settings.TG_REPORTS_CHAT)
async def balance(message: Message):
    picture = await Actions.take_screenshot_of_region(
        WorkspaceCoords.BALANCE_WINDOW_TOP_LEFT, WorkspaceCoords.BALANCE_WINDOW_BOTTOM_RIGHT
    )
    await message.answer_photo(picture)
