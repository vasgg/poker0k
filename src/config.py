from logging.handlers import RotatingFileHandler
import sys
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from internal import Stage


class Settings(BaseSettings):
    ENCRYPT_KEY: SecretStr
    DECRYPT_KEY: SecretStr
    TEST_ENDPOINT: str
    MAX_ATTEMPTS: int
    STAGE: Stage
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASSWORD: SecretStr
    DB_NAME: str
    RESTARTS_AT: list[int]
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_PASSWORD: SecretStr
    TG_BOT_TOKEN: SecretStr
    TG_ID: int

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', case_sensitive=False, extra='allow')

    @property
    def key_decrypt(self) -> bytes:
        return self.DECRYPT_KEY.get_secret_value()[:32].encode()

    @property
    def key_encrypt(self) -> bytes:
        return self.ENCRYPT_KEY.get_secret_value()[:32].encode()


settings = Settings()


def get_logging_config(app_name: str):
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "main": {
                "format": "%(asctime)s [%(funcName)15s:%(lineno)-3d] %(message)s",
                "datefmt": "%d.%m.%Y %H:%M:%S",
            },
            "errors": {
                "format": "%(asctime)s [%(funcName)15s:%(lineno)-3d] %(message)s",
                "datefmt": "%d.%m.%Y %H:%M:%S",
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
                "filename": f"logs/{app_name}_log.log",
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
