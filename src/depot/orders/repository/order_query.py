"""Read side of the orders storage: what a discount code is worth.

The counter asks this before it prints a quote, so the answer has to come from
one lookup. The codes themselves are held in memory and reloaded when the
marketing list changes.
"""

import depot.core.ports
import depot.orders.models.discount_models

DiscountRecord = depot.orders.models.discount_models.Discount
"""The record type this query hands out.

The layers above the repository do not reach into the models package, so they
name the type through here.
"""


class OrderQuery(depot.core.ports.DiscountCatalog):
    """Answers the discount questions the counter and the services ask."""

    def __init__(self) -> None:
        self._by_code: dict[str, DiscountRecord] = {
            discount.code: discount
            for discount in depot.orders.models.discount_models.house_codes()
        }

    def percent_for(self, code: str, subtotal_cents: int) -> int:
        """Report the percentage a code takes off a subtotal, 0 if it does not."""
        discount = self._by_code.get(code.strip().upper())
        if discount is None:
            return 0
        if not discount.applies_to(subtotal_cents, ""):
            return 0
        return discount.percent

    def cut_cents(self, code: str, subtotal_cents: int, zone: str) -> int:
        """Report what a code takes off a subtotal in a given zone."""
        discount = self._by_code.get(code.strip().upper())
        if discount is None or not discount.applies_to(subtotal_cents, zone):
            return 0
        return discount.cut_cents(subtotal_cents)

    def find(self, code: str) -> DiscountRecord | None:
        """Return one discount code, or None if the depot does not honour it."""
        return self._by_code.get(code.strip().upper())

    def codes_for_zone(self, zone: str) -> list[str]:
        """List the codes that can be used on shipments into a zone."""
        return sorted(
            discount.code
            for discount in self._by_code.values()
            if not discount.zones or zone in discount.zones
        )

    def reload(self, discounts: list[DiscountRecord]) -> int:
        """Replace the code list and report how many codes are now honoured."""
        self._by_code = {discount.code: discount for discount in discounts}
        return len(self._by_code)
