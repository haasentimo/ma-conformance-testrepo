"""Read side of the billing storage: what has been paid on an invoice.

The payments arrive as a bank statement and carry whatever remittance reference
the customer typed. Matching them onto invoice numbers is the work this module
does, and it is the only place that knows how wrong a reference may be before
the depot gives up and books it to the clearing account.
"""

import depot.core.ports
import depot.billing.models.payment_models

PaymentRecord = depot.billing.models.payment_models.Payment
"""The record type this query hands out.

The layers above the repository do not reach into the models package, so they
name the type through here.
"""

CLEARING_ACCOUNT: str = "unmatched"


class InvoiceQuery(depot.core.ports.PaymentLedger):
    """Answers what has been paid, and against which invoice."""

    def __init__(self) -> None:
        self._by_invoice: dict[str, list[PaymentRecord]] = {}

    def settled_cents(self, invoice_number: str) -> int:
        """Report how much of an invoice has already been settled."""
        return sum(
            payment.amount_cents
            for payment in self._by_invoice.get(invoice_number, ())
        )

    def book(self, payment: PaymentRecord, known_numbers: list[str]) -> str:
        """File a payment against an invoice and report where it went.

        A reference that matches nothing is not dropped — it goes to the
        clearing account, where the bookkeeping picks it up by hand. Losing a
        payment because a customer mistyped a digit is not an option.
        """
        target = self.match(payment, known_numbers)
        self._by_invoice.setdefault(target, []).append(payment)
        return target

    def match(self, payment: PaymentRecord, known_numbers: list[str]) -> str:
        """Report which invoice a payment belongs to, or the clearing account."""
        if not payment.looks_matchable():
            return CLEARING_ACCOUNT
        if payment.reference in known_numbers:
            return payment.reference
        for number in known_numbers:
            if number and number.upper() in payment.remittance_note.upper():
                return number
        return CLEARING_ACCOUNT

    def payments_of(self, invoice_number: str) -> list[PaymentRecord]:
        """List the payments booked against an invoice, oldest first."""
        return sorted(
            self._by_invoice.get(invoice_number, ()),
            key=lambda payment: payment.received_at,
        )

    def unmatched_cents(self) -> int:
        """Report how much money is sitting on the clearing account."""
        return self.settled_cents(CLEARING_ACCOUNT)

    def last_payment_at(self, invoice_number: str) -> float | None:
        """Report when money last arrived for an invoice, or None."""
        payments = self.payments_of(invoice_number)
        if not payments:
            return None
        return payments[-1].received_at
