class ProductService:

    async def resolve_product(
        self,
        query: str,
        customer_id: int | None
    ):

        products = {
            "fries": {
                "product_id": 101,
                "product_name": "French Fries 6mm",
                "unit_price": 1100,
                "available_quantity": 20  # Demo stock, not live inventory
            },

            "milk": {
                "product_id": 201,
                "product_name": "Milk 1L",
                "unit_price": 80,
                "available_quantity": 50  # Demo stock, not live inventory
            }
        }

        product = products.get(
            query.lower()
        )

        if not product:
            return {
                "status": "not_found"
            }

        return {
            "status": "resolved",
            "product": product
        }


product_service = ProductService()
