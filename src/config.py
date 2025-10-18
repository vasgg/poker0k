from datetime import datetime
import socket
import logging.config
from logging import Formatter
from logging.handlers import RotatingFileHandler
from pathlib import Path
import sys
from bot.handlers import router as main_router

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.client.session.aiohttp import AiohttpSession
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from bot.helpers import on_shutdown, on_startup
from internal.schemas import Stage


class Settings(BaseSettings):
    ENCRYPT_KEY: SecretStr
    DECRYPT_KEY: SecretStr
    MAX_ATTEMPTS: int
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASSWORD: SecretStr
    DB_NAME: str
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_PASSWORD: SecretStr
    TG_BOT_TOKEN: SecretStr
    TG_BOT_ADMIN_ID: int
    TG_REPORTS_CHAT: int
    NGROK_URL: SecretStr
    NGROK_USER: SecretStr
    NGROK_PASSWORD: SecretStr
    RESET_AFTER_MINS: int
    STAGE: Stage

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="allow")

    @property
    def key_decrypt(self) -> bytes:
        return self.DECRYPT_KEY.get_secret_value()[:32].encode()

    @property
    def key_encrypt(self) -> bytes:
        return self.ENCRYPT_KEY.get_secret_value()[:32].encode()


settings = Settings()


def setup_worker(app_name: str):
    Path("logs").mkdir(parents=True, exist_ok=True)
    Path("screenshots").mkdir(parents=True, exist_ok=True)
    logging_config = get_logging_config(app_name)
    logging.config.dictConfig(logging_config)


def setup_bot():
    session = AiohttpSession()
    session._connector_init["family"] = socket.AF_INET
    bot = Bot(
        token=settings.TG_BOT_TOKEN.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        session=session,
    )
    dispatcher = Dispatcher(settings=settings)
    dispatcher.startup.register(on_startup)
    dispatcher.shutdown.register(on_shutdown)
    # dispatcher.startup.register(set_bot_commands)

    # dispatcher.update.outer_middleware(UpdatesDumperMiddleware())
    # dispatcher.message.middleware.register(LoggingMiddleware())

    dispatcher.include_router(main_router)
    return bot, dispatcher


class CustomFormatter(Formatter):
    def formatTime(self, record, datefmt=None):
        ct = datetime.fromtimestamp(record.created).astimezone()
        if datefmt:
            base_time = ct.strftime("%d.%m.%Y %H:%M:%S")
            msecs = f"{int(record.msecs):03d}"
            tz = ct.strftime("%z")
            return f"{base_time}.{msecs}{tz}"
        else:
            return super().formatTime(record, datefmt)


main_template = {
    "format": "%(asctime)s | %(message)s",
    "datefmt": "%d.%m.%Y %H:%M:%S%z",
}
error_template = {
    "format": "%(asctime)s [%(levelname)8s] [%(module)s:%(funcName)s:%(lineno)d] %(message)s",
    "datefmt": "%d.%m.%Y %H:%M:%S%z",
}


def get_logging_config(app_name: str):
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "main": {
                "()": CustomFormatter,
                "format": main_template["format"],
                "datefmt": main_template["datefmt"],
            },
            "errors": {
                "()": CustomFormatter,
                "format": error_template["format"],
                "datefmt": error_template["datefmt"],
            },
        },
        "handlers": {
            "stdout": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "main",
                "stream": sys.stdout,
            },
            "stderr": {
                "class": "logging.StreamHandler",
                "level": "WARNING",
                "formatter": "errors",
                "stream": sys.stderr,
            },
            "file": {
                "()": RotatingFileHandler,
                "level": "INFO",
                "formatter": "main",
                "filename": f"logs/{app_name}.log",
                "maxBytes": 50000000,
                "backupCount": 3,
                "encoding": "utf-8",
            },
        },
        "loggers": {
            "root": {
                "level": "DEBUG",
                "handlers": ["stdout", "stderr", "file"],
            },
        },
    }
