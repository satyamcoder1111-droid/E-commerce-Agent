from typing import Annotated, Any, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

from models.order import RequestedItem, CartItem


class EcommerceState(TypedDict):

    messages: Annotated[
        list[BaseMessage],
        add_messages
    ]

    # Customer
    customer_id: int | None

    # Products requested in the latest customer message
    requested_items: list[RequestedItem]

    # Validated cart
    cart_items: list[CartItem]

    # Order information tracking
    required_fields: list[str]
    collected_fields: list[str]
    pending_fields: list[str]

    # Whether the customer has finished adding products
    cart_complete: bool | None

    # Delivery
    delivery_date: str | None

    # Last inventory validation
    inventory_result: dict[str, Any] | None

    # Final confirmation
    order_confirmed: bool

    # Final order result
    order_id: int | None
    total_amount: float | None

    # Error
    error: str | None