import asyncio

from langchain_core.messages import HumanMessage

from agent.graph import graph


async def main():

    config = {
        "configurable": {
            "thread_id": "customer-123"
        }
    }

    initial_state = {
        "messages": [
            HumanMessage(
                content="fries 2 ctn milk 4 pct"
            )
        ],

        "customer_id": 123,

        "requested_items": [],
        "cart_items": [],

        "required_fields": [
            "customer_id",
            "items",
            "cart_complete",
            "delivery_date",
            "confirmation",
        ],

        "collected_fields": [
            "customer_id"
        ],

        "pending_fields": [
            "items",
            "cart_complete",
            "delivery_date",
            "confirmation",
        ],

        "cart_complete": None,

        "delivery_date": None,

        "inventory_result": None,

        "order_confirmed": False,

        "order_id": None,

        "total_amount": None,

        "error": None,
    }


    result = await graph.ainvoke(
        initial_state,
        config=config
    )


    print("\nBOT RESPONSE:")
    print(
        result["messages"][-1].content
    )


    print("\nCART:")
    for item in result["cart_items"]:
        print(item)


    print("\nCOLLECTED FIELDS:")
    print(
        result["collected_fields"]
    )


    print("\nPENDING FIELDS:")
    print(
        result["pending_fields"]
    )


if __name__ == "__main__":
    asyncio.run(main())