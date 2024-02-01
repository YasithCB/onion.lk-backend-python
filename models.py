from pydantic import BaseModel
from decimal import Decimal


class Order(BaseModel):
    description: str
    storeName: str
    maxBudget: float