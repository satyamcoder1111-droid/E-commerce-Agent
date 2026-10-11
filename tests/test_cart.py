"""Test cart state transitions without invoking a language model."""

import unittest
from types import SimpleNamespace

from agent.tools import update_cart
from models.order import RequestedItem


class CartTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.state = {
            "customer_id": 123, "cart_items": [],
            "required_fields": ["items", "cart_complete", "confirmation"],
            "collected_fields": [], "cart_complete": False,
            "order_confirmed": False,
        }

    async def update(self, **fields):
        result = await update_cart.coroutine(
            items=[RequestedItem(**fields)],
            runtime=SimpleNamespace(state=self.state, tool_call_id="test-call"),
        )
        self.state.update(result.update)
        return self.state["inventory_result"]["items"][0]["status"]

    async def add_fries(self):
        return await self.update(product_query="fries", quantity=2, unit="carton")

    async def test_add_accumulates_quantity_and_updates_total(self):
        self.assertEqual(await self.add_fries(), "added")
        self.assertEqual(await self.add_fries(), "updated")
        item = self.state["cart_items"][0]
        self.assertEqual(item.quantity, 4)
        self.assertEqual(item.total_price, 4400)

    async def test_set_quantity_replaces_quantity_and_preserves_unit(self):
        await self.add_fries()
        self.assertEqual(await self.update(product_query="fries", action="set_quantity", quantity=5), "updated")
        item = self.state["cart_items"][0]
        self.assertEqual(item.quantity, 5)
        self.assertEqual(item.unit, "carton")
        self.assertEqual(item.total_price, 5500)

    async def test_remove_needs_no_quantity_or_unit(self):
        await self.add_fries()
        self.assertEqual(await self.update(product_query="fries", action="remove"), "removed")
        self.assertEqual(self.state["cart_items"], [])
        self.assertIn("items", self.state["pending_fields"])

    async def test_remove_missing_item(self):
        self.assertEqual(await self.update(product_query="fries", action="remove"), "not_in_cart")

    async def test_stock_rejection_preserves_cart(self):
        await self.add_fries()
        self.assertEqual(await self.update(product_query="fries", action="set_quantity", quantity=100), "insufficient_stock")
        self.assertEqual(self.state["cart_items"][0].quantity, 2)

    async def test_required_quantity_and_unit(self):
        self.assertEqual(await self.update(product_query="fries"), "missing_quantity")
        self.assertEqual(await self.update(product_query="fries", quantity=2), "missing_unit")
        self.assertEqual(self.state["cart_items"], [])

    async def test_cart_change_invalidates_confirmation(self):
        await self.add_fries()
        self.state.update(cart_complete=True, order_confirmed=True,
                          collected_fields=["items", "cart_complete", "confirmation"])
        await self.update(product_query="fries", action="set_quantity", quantity=3)
        self.assertFalse(self.state["cart_complete"])
        self.assertFalse(self.state["order_confirmed"])
        self.assertIn("confirmation", self.state["pending_fields"])


if __name__ == "__main__":
    unittest.main()
