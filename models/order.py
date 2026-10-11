from typing import Literal
from pydantic import BaseModel, Field


class RequestedItem(BaseModel):
    product_query: str

    action: Literal[
        "add",
        "remove",
        "set_quantity"
    ] = "add"

    quantity: float | None = Field(
        default=None,
        gt=0
    )

    unit: str | None = None


class CartItem(BaseModel):
    product_id: int

    product_name: str

    quantity: float

    unit: str

    unit_price: float

    total_price: float