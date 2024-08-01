from enum import StrEnum, auto

from pydantic import BaseModel


class Task(BaseModel):
    order_id: int
    user_id: int
    requisite: str
    amount: float
    status: int
    callback_url: str


class Stage(StrEnum):
    DEV = auto()
    PROD = auto()
