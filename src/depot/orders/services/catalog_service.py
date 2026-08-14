"""What a shipment costs before it is booked.

The counter quotes from two sources: the carrier tariff, which the depot does
not own and asks for through a port, and the discount codes it honours itself.
Both are read-only — a quote writes nothing.
"""

import depot.core.ports
import depot.orders.repository.order_query


class CatalogService:
    """Answers what a shipment into a zone would cost."""

    def __init__(self, discounts: depot.orders.repository.order_query.OrderQuery) -> None:
        self.discounts: depot.orders.repository.order_query.OrderQuery = discounts

    def quote_cents(
        self,
        zone: str,
        weight_grams: int,
        rates: depot.core.ports.RateProvider,
    ) -> int:
        """Quote one parcel at the carrier tariff, before any discount."""
        if weight_grams <= 0:
            return 0
        return rates.rate_cents(zone, weight_grams)

    def net_cents(self, zone: str, subtotal_cents: int, code: str) -> int:
        """Report what is left of a subtotal after a discount code."""
        return subtotal_cents - self.discounts.cut_cents(code, subtotal_cents, zone)

    def offers_for(self, zone: str) -> list[str]:
        """List the discount codes a shipment into a zone can use."""
        return self.discounts.codes_for_zone(zone)

    def honours(self, code: str) -> bool:
        """Report whether the depot honours a code at all."""
        return self.discounts.find(code) is not None
