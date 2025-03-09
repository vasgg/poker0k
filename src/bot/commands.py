from aiogram import Bot, types

default_commands = [
    # types.BotCommand(command="/run-worker", description="start worker"),
    # types.BotCommand(command="/stop-worker", description="stop worker"),
    types.BotCommand(command="/balance", description="get balance"),
]


async def set_bot_commands(bot: Bot) -> None:
    await bot.set_my_commands(default_commands)
