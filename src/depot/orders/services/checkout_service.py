"""Hand-over of the parcels at the counter.

Checkout is the moment the customer lets go of the parcels: every line is
weighed and checked, the depot reserves a shelf slot for the lot, and from then
on the parcels are the depot's problem. Nothing here talks to money — what the
shipment costs was settled on the quote.
"""

import depot.core.ports
import depot.billing.services.invoice_service
import depot.orders.repository.order_line_repo


class CheckoutService:
    """Takes the parcels of an order over the counter."""

    def __init__(
        self,
        lines: depot.orders.repository.order_line_repo.OrderLineRepository,
        shelves: depot.core.ports.ShelfAllocator,
    ) -> None:
        self.lines: depot.orders.repository.order_line_repo.OrderLineRepository = lines
        self.shelves: depot.core.ports.ShelfAllocator = shelves
        self._slots: dict[str, str] = {}

    def hand_over(self, order_reference: str, depot_code: str) -> str:
        """Take an order over the counter and return the shelf slot it went to.

        An order without a parcel gets no slot: there is nothing to put away,
        and a reserved slot nobody fills blocks the aisle for the rest of the
        shift.
        """
        parcels = self.lines.of_order(order_reference)
        if not parcels:
            return ""
        slot = self.shelves.reserve(depot_code, len(parcels))
        self._slots[order_reference] = slot
        return slot

    def slot_of(self, order_reference: str) -> str | None:
        """Return the shelf slot an order was put away in, or None."""
        return self._slots.get(order_reference)

    def take_back(self, order_reference: str) -> bool:
        """Give the parcels back and free the slot; report whether it existed."""
        slot = self._slots.pop(order_reference, None)
        if slot is None:
            return False
        return self.shelves.release(slot)

    def two_hand_warning(self, order_reference: str) -> list[str]:
        """List the parcels the packer must not lift alone."""
        return self.lines.two_hand_lines(order_reference)

    def handed_weight_grams(self, order_reference: str) -> int:
        """Report what the depot just took over, in grams."""
        return self.lines.weight_grams(order_reference)

    def bill_after_handover(
        self,
        order_reference: str,
        customer_reference: str,
        net_cents: int,
        invoices: depot.billing.services.invoice_service.InvoiceService,
    ) -> str:
        """Raise the invoice for a lot the depot has just taken over."""
        if self.slot_of(order_reference) is None:
            return ""
        return invoices.raise_invoice(
            customer_reference, order_reference, net_cents
        )
