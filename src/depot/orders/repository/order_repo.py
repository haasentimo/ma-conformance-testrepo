"""Storage of the order headers.

The repository mints the order reference before the first write, because the
counter prints it on the acceptance slip while the customer is still standing
there.
"""

import depot.core.ports
import depot.orders.models.order_models
import depot.orders.services.order_service

OrderRecord = depot.orders.models.order_models.Order
"""The record type this repository hands out.

The layers above the repository do not reach into the models package, so they
name the type through here.
"""


class OrderRepository:
    """Reads and writes the order headers."""

    def __init__(self, ids: depot.core.ports.IdGenerator) -> None:
        self.ids: depot.core.ports.IdGenerator = ids
        self._by_reference: dict[str, OrderRecord] = {}

    def create(self, customer_reference: str, destination_zone: str) -> str:
        """Open a draft order and return the reference it was filed under."""
        order = depot.orders.models.order_models.Order()
        order.customer_reference = customer_reference
        order.destination_zone = destination_zone
        order.status = depot.orders.models.order_models.STATUS_DRAFT
        order.line_count = 0
        order.total_cents = 0
        reference = self.ids.new_id("ord")
        order.reference = reference
        self._by_reference[reference] = order
        return reference

    def get(self, reference: str) -> OrderRecord | None:
        """Return the order filed under a reference, or None."""
        return self._by_reference.get(reference)

    def place(self, reference: str, placed_at: float) -> bool:
        """Hand an order over to dispatch; report whether it was there.

        What follows from a placed order — the dispatch manifest, telling the
        customer, the invoice — happens above this layer.
        """
        order = self._by_reference.get(reference)
        if order is None:
            return False
        order.place(placed_at)
        return True

    def cancel(self, reference: str) -> bool:
        """Withdraw an order; report whether the reference was known."""
        order = self._by_reference.get(reference)
        if order is None:
            return False
        order.cancel()
        return True

    def book_line(self, reference: str, amount_cents: int) -> bool:
        """Book one parcel onto the header totals."""
        order = self._by_reference.get(reference)
        if order is None:
            return False
        order.add_line_total(amount_cents)
        return True

    def open_of_customer(self, customer_reference: str) -> list[str]:
        """List the references a customer still has running."""
        return sorted(
            reference
            for reference, order in self._by_reference.items()
            if order.customer_reference == customer_reference and order.is_open()
        )

    def count(self) -> int:
        """Report how many orders are on file."""
        return len(self._by_reference)

    def placed_notice_template(self) -> str:
        """Report the notice that goes out when an order is placed."""
        return depot.orders.services.order_service.PLACED_TEMPLATE
