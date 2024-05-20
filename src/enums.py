from enum import Enum

from pydantic import BaseModel


class Status(Enum):
    SUCCESS = 1
    FAIL = 0


class Task(BaseModel):
    order_id: int
    user_id: int
    requisite: str
    amount: float
    status: int
