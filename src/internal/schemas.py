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
    message: str | None = None
    step: Step | None = None


class CheckType(StrEnum):
    MONEY = auto()
    NAME = auto()


class Section(StrEnum):
    TRANSFER_BUTTON = auto()
    TRANSFER_CONFIRM_BUTTON = auto()
    TRANSFER_CONFIRM_SECTION = auto()


class ErrorType(StrEnum):
    INSUFFICIENT_FUNDS = auto()
    INCORRECT_NAME = auto()
