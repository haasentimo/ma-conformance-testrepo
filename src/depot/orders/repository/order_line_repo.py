"""Storage of the order lines — one row per physical parcel."""

import depot.core.ports
import depot.orders.models.order_line_models

OrderLineRecord = depot.orders.models.order_line_models.OrderLine
"""The record type this repository hands out.

The layers above the repository do not reach into the models package, so they
name the type through here.
"""


class OrderLineRepository:
    """Reads and writes the parcels of an order."""

    def __init__(self, ids: depot.core.ports.IdGenerator) -> None:
        self.ids: depot.core.ports.IdGenerator = ids
        self._by_reference: dict[str, OrderLineRecord] = {}

    def add(
        self,
        order_reference: str,
        description: str,
        weight_grams: int,
        quantity: int,
        unit_price_cents: int,
        fragile: bool = False,
    ) -> str:
        """File one parcel of an order and return its line reference."""
        line = depot.orders.models.order_line_models.OrderLine()
        line.order_reference = order_reference
        line.description = description
        line.weight_grams = weight_grams
        line.quantity = quantity
        line.unit_price_cents = unit_price_cents
        line.fragile = fragile
        line.check()
        reference = self.ids.new_id("line")
        line.reference = reference
        self._by_reference[reference] = line
        return reference

    def get(self, reference: str) -> OrderLineRecord | None:
        """Return one line, or None if the reference is unknown."""
        return self._by_reference.get(reference)

    def of_order(self, order_reference: str) -> list[OrderLineRecord]:
        """List the parcels of an order, in the order they were handed in."""
        return [
            line
            for line in self._by_reference.values()
            if line.order_reference == order_reference
        ]

    def drop(self, reference: str) -> bool:
        """Take a parcel back off an order before it was placed."""
        return self._by_reference.pop(reference, None) is not None

    def subtotal_cents(self, order_reference: str) -> int:
        """Report what the parcels of an order come to before any discount."""
        return sum(line.total_cents() for line in self.of_order(order_reference))

    def weight_grams(self, order_reference: str) -> int:
        """Report what the parcels of an order weigh together."""
        return sum(line.total_weight_grams() for line in self.of_order(order_reference))

    def two_hand_lines(self, order_reference: str) -> list[str]:
        """List the parcels of an order that are a two-person lift."""
        return sorted(
            line.reference
            for line in self.of_order(order_reference)
            if line.needs_two_hands()
        )
