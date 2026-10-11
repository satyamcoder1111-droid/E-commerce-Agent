import asyncio

from services.product_service import product_service

print(
    asyncio.run(
        product_service.resolve_product(
            "fries",
            123
        )
    )
)
