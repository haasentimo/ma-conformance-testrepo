"""Money back for a shipment the depot did not carry out.

A refund is only ever due on a cancelled order, and only for what was actually
taken. The money itself moves outside the depot; this service decides the
amount and hands it to the gateway.
"""

import depot.orders.repository.order_repo

CANCELLATION_FEE_CENTS: int = 300


class RefundService:
    """Works out and triggers the refunds of cancelled orders."""

    def __init__(self, orders: depot.orders.repository.order_repo.OrderRepository) -> None:
        self.orders: depot.orders.repository.order_repo.OrderRepository = orders

    def refund(
        self,
        reference: str,
        payment_reference: str,
        gateway: object,
    ) -> str:
        """Refund a cancelled order and return the gateway's receipt.

        An order that is not cancelled, or one that owes nothing, gets no
        receipt — an empty string tells the caller nothing moved.
        """
        amount = self.refundable_cents(reference)
        if amount <= 0:
            return ""
        return gateway.refund(payment_reference, amount)

    def refundable_cents(self, reference: str) -> int:
        """Report what the depot owes back on an order, fee deducted."""
        order = self.orders.get(reference)
        if order is None or order.is_open():
            return 0
        return max(0, order.total_cents - CANCELLATION_FEE_CENTS)

    def fee_cents(self, reference: str) -> int:
        """Report the fee the depot keeps for a cancellation."""
        if self.refundable_cents(reference) <= 0:
            return 0
        return CANCELLATION_FEE_CENTS
