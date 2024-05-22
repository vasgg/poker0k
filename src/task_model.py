from pydantic import BaseModel


class Task(BaseModel):
    order_id: int
    user_id: int
    requisite: str
    amount: float
    status: int
