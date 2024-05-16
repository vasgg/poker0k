from ipaddress import IPv4Address
from logging.handlers import RotatingFileHandler

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from enums import Stage


class Settings(BaseSettings):
    ENCRYPT_KEY: SecretStr
    DECRYPT_KEY: SecretStr
    REPORT_ENDPOINT: IPv4Address

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')


settings = Settings()


def get_logging_config(app_name: str):
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "main": {
                "format": "%(asctime)s.%(msecs)03d|%(levelname)s|%(module)s|%(funcName)s: %(message)s",
                "datefmt": "%d.%m.%Y %H:%M:%S:%z",
            },
            "errors": {
                "format": "%(asctime)s.%(msecs)03d|%(levelname)s|%(module)s|%(funcName)s|L%(lineno)d: %(message)s",
                "datefmt": "%d.%m.%Y %H:%M:%S%z",
            },
        },
        "handlers": {
            "stdout": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "main",
                "stream": "ext://sys.stdout",
            },
            "stderr": {
                "class": "logging.StreamHandler",
                "level": "WARNING",
                "formatter": "errors",
                "stream": "ext://sys.stderr",
            },
            "file": {
                "()": RotatingFileHandler,
                "level": "INFO",
                "formatter": "main",
                "filename": f"logs/{app_name}_log.log",
                "maxBytes": 500000,
                "backupCount": 3,
            },
        },
        "loggers": {
            "root": {
                "level": "DEBUG",
                "handlers": ["stdout", "stderr", "file"],
            },
        },
    }
