from enum import StrEnum, auto

from pydantic import BaseModel


class Step(StrEnum):
    REPORT_FAILED = auto()
    FAILED = auto()
    ACCEPTED = auto()
    PROCESSED = auto()
    REPORTED = auto()


class Task(BaseModel):
    order_id: int
    user_id: int
    requisite: str
    amount: float
    status: int
    callback_url: str
    message: str
    step: Step | None = None


class Stage(StrEnum):
    DEV = auto()
    PROD = auto()
