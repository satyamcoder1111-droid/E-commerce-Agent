import json

from langchain_core.tools import tool
from langchain.tools import ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from models.order import RequestedItem, CartItem
from services.product_service import product_service

@tool
async def update_cart(
    items: list[RequestedItem],
    runtime: ToolRuntime
) -> Command:
    """
    Add, remove, or update quantities of products in the cart.

    Actions:
    - add
    - remove
    - set_quantity
    """

    cart_items = list(
        runtime.state.get("cart_items", [])
    )

    results = []
    cart_changed = False

    for item in items:

        # Resolve product

        resolution = await product_service.resolve_product(
            query=item.product_query,
            customer_id=runtime.state.get("customer_id")
        )

        if resolution["status"] != "resolved":
            results.append({
                "product_query": item.product_query,
                "status": resolution["status"],
                "options": resolution.get("options", [])
            })
            continue

        product = resolution["product"]

        product_id = product["product_id"]
        product_name = product["product_name"]
        unit_price = product["unit_price"]
        available_quantity = product["available_quantity"]

        # Find existing product

        existing_item = next(
            (
                cart_item
                for cart_item in cart_items
                if cart_item.product_id == product_id
            ),
            None
        )

        # REMOVE

        if item.action == "remove":

            if existing_item is None:
                results.append({
                    "product_id": product_id,
                    "product_name": product_name,
                    "status": "not_in_cart"
                })
                continue

            cart_items.remove(existing_item)

            cart_changed = True

            results.append({
                "product_id": product_id,
                "product_name": product_name,
                "status": "removed"
            })

            continue

        # ADD

        if item.action == "add":

            if item.quantity is None:
                results.append({
                    "product_query": item.product_query,
                    "status": "missing_quantity"
                })
                continue

            if item.unit is None:
                results.append({
                    "product_query": item.product_query,
                    "status": "missing_unit"
                })
                continue

            existing_quantity = (
                existing_item.quantity
                if existing_item
                else 0
            )

            final_quantity = (
                existing_quantity
                + item.quantity
            )

            if available_quantity < final_quantity:
                results.append({
                    "product_id": product_id,
                    "product_name": product_name,
                    "status": "insufficient_stock",
                    "requested_quantity": final_quantity,
                    "available_quantity": available_quantity
                })
                continue

            if existing_item:

                existing_item.quantity = final_quantity
                existing_item.unit_price = unit_price
                existing_item.total_price = (
                    final_quantity * unit_price
                )

                status = "updated"

            else:

                cart_item = CartItem(
                    product_id=product_id,
                    product_name=product_name,
                    quantity=item.quantity,
                    unit=item.unit,
                    unit_price=unit_price,
                    total_price=item.quantity * unit_price
                )

                cart_items.append(cart_item)

                status = "added"

            cart_changed = True

            results.append({
                "product_id": product_id,
                "product_name": product_name,
                "quantity": final_quantity,
                "unit": item.unit,
                "status": status
            })

            continue

        # SET QUANTITY

        if item.action == "set_quantity":

            if existing_item is None:
                results.append({
                    "product_id": product_id,
                    "product_name": product_name,
                    "status": "not_in_cart"
                })
                continue

            if item.quantity is None:
                results.append({
                    "product_query": item.product_query,
                    "status": "missing_quantity"
                })
                continue

            if available_quantity < item.quantity:
                results.append({
                    "product_id": product_id,
                    "product_name": product_name,
                    "status": "insufficient_stock",
                    "requested_quantity": item.quantity,
                    "available_quantity": available_quantity
                })
                continue

            existing_item.quantity = item.quantity

            # Preserve the existing unit when no replacement is provided.
            if item.unit is not None:
                existing_item.unit = item.unit

            existing_item.unit_price = unit_price

            existing_item.total_price = (
                item.quantity * unit_price
            )

            cart_changed = True

            results.append({
                "product_id": product_id,
                "product_name": product_name,
                "quantity": item.quantity,
                "unit": existing_item.unit,
                "status": "updated"
            })

    # Collected / pending fields

    collected_fields = list(
        runtime.state.get(
            "collected_fields",
            []
        )
    )

    if cart_items:

        if "items" not in collected_fields:
            collected_fields.append("items")

    else:

        if "items" in collected_fields:
            collected_fields.remove("items")

    # Cart changes invalidate previous completion and confirmation.
    if cart_changed:

        if "cart_complete" in collected_fields:
            collected_fields.remove("cart_complete")

        if "confirmation" in collected_fields:
            collected_fields.remove("confirmation")

    required_fields = runtime.state.get(
        "required_fields",
        []
    )

    pending_fields = [
        field
        for field in required_fields
        if field not in collected_fields
    ]

    return Command(
        update={
            "requested_items": items,
            "cart_items": cart_items,

            "inventory_result": {
                "items": results
            },

            "cart_complete": (
                False
                if cart_changed
                else runtime.state.get("cart_complete")
            ),

            "order_confirmed": (
                False
                if cart_changed
                else runtime.state.get(
                    "order_confirmed",
                    False
                )
            ),

            "collected_fields": collected_fields,
            "pending_fields": pending_fields,

            "messages": [
                ToolMessage(
                    content=json.dumps({
                        "results": results
                    }),
                    tool_call_id=runtime.tool_call_id
                )
            ]
        }
    ) 
@tool
def capture_information(
    runtime: ToolRuntime,

    customer_id: int | None = None,

    delivery_date: str | None = None,

    cart_complete: bool | None = None,

    order_confirmed: bool | None = None

) -> Command:
    """
    Save order-related information into the graph state.

    Use this when the customer provides or changes:
    - customer id
    - delivery date
    - whether they want to add more items
    - final order confirmation
    """

    updates = {}

    captured = []

    collected_fields = list(
        runtime.state.get(
            "collected_fields",
            []
        )
    )

    # Customer

    if customer_id is not None:

        updates["customer_id"] = customer_id

        if "customer_id" not in collected_fields:
            collected_fields.append(
                "customer_id"
            )

        captured.append(
            "customer_id"
        )

    # Delivery date

    if delivery_date is not None:

        updates["delivery_date"] = (
            delivery_date
        )

        if "delivery_date" not in collected_fields:
            collected_fields.append(
                "delivery_date"
            )

        captured.append(
            "delivery_date"
        )

    # Cart complete

    if cart_complete is not None:

        updates["cart_complete"] = (
            cart_complete
        )

        if cart_complete:

            if "cart_complete" not in collected_fields:
                collected_fields.append(
                    "cart_complete"
                )

        else:

            if "cart_complete" in collected_fields:
                collected_fields.remove(
                    "cart_complete"
                )

        captured.append(
            "cart_complete"
        )

    # Order confirmation

    if order_confirmed is not None:

        updates["order_confirmed"] = (
            order_confirmed
        )

        if order_confirmed:

            if "confirmation" not in collected_fields:
                collected_fields.append(
                    "confirmation"
                )

        else:

            if "confirmation" in collected_fields:
                collected_fields.remove(
                    "confirmation"
                )

        captured.append(
            "confirmation"
        )

    # Calculate pending fields

    required_fields = runtime.state.get(
        "required_fields",
        []
    )

    pending_fields = [
        field
        for field in required_fields
        if field not in collected_fields
    ]

    updates["collected_fields"] = (
        collected_fields
    )

    updates["pending_fields"] = (
        pending_fields
    )

    # Tool response

    updates["messages"] = [
        ToolMessage(
            content=json.dumps({
                "status": "updated",

                "captured": captured,

                "collected_fields":
                    collected_fields,

                "pending_fields":
                    pending_fields
            }),

            tool_call_id=runtime.tool_call_id
        )
    ]

    return Command(
        update=updates
    )
