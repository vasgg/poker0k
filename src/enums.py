from enum import StrEnum, auto

from pydantic import BaseModel


class Stage(StrEnum):
    DEV = auto()
    PROD = auto()


class Status(StrEnum):
    SUCCESS = auto()
    FAIL = auto()


class Task(BaseModel):
    nickname: str
    amount: int
