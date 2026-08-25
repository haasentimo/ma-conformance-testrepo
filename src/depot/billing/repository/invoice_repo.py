"""Storage of the invoices.

The repository mints the invoice number before the first write: the number goes
onto the paper the same run that raises the invoice, and a gap in the sequence
is something the auditor asks about.
"""

import depot.core.ports
import depot.billing.models.invoice_models
import depot.billing.services.invoice_service

InvoiceRecord = depot.billing.models.invoice_models.Invoice
"""The record type this repository hands out.

The layers above the repository do not reach into the models package, so they
name the type through here.
"""


class InvoiceRepository:
    """Reads and writes the invoices."""

    def __init__(self, ids: depot.core.ports.IdGenerator) -> None:
        self.ids: depot.core.ports.IdGenerator = ids
        self._by_number: dict[str, InvoiceRecord] = {}

    def create(
        self, customer_reference: str, order_reference: str, net_cents: int
    ) -> str:
        """Draft an invoice for a shipment and return its number."""
        invoice = depot.billing.models.invoice_models.Invoice()
        invoice.customer_reference = customer_reference
        invoice.order_reference = order_reference
        invoice.net_cents = net_cents
        invoice.status = depot.billing.models.invoice_models.STATUS_DRAFT
        invoice.settled_cents = 0
        invoice.reminders_sent = 0
        invoice.terms_days = depot.billing.models.invoice_models.DEFAULT_TERMS_DAYS
        number = self.ids.new_id("inv")
        invoice.number = number
        self._by_number[number] = invoice
        return number

    def get(self, number: str) -> InvoiceRecord | None:
        """Return the invoice filed under a number, or None."""
        return self._by_number.get(number)

    def issue(self, number: str, issued_at: float) -> bool:
        """Raise an invoice; report whether the number was known.

        What follows from a raised invoice — sending it out, the reminders, the
        ledger posting — happens above this layer.
        """
        invoice = self._by_number.get(number)
        if invoice is None:
            return False
        invoice.issue(issued_at)
        return True

    def settle(self, number: str, amount_cents: int) -> int:
        """Book money against an invoice and report what stays open."""
        invoice = self._by_number.get(number)
        if invoice is None:
            return 0
        return invoice.settle(amount_cents)

    def count_reminder(self, number: str) -> int:
        """Note that a reminder went out and report how many that makes."""
        invoice = self._by_number.get(number)
        if invoice is None:
            return 0
        invoice.reminders_sent += 1
        return invoice.reminders_sent

    def overdue(self, now_epoch: float) -> list[str]:
        """List the invoice numbers whose payment term has run out."""
        return sorted(
            number
            for number, invoice in self._by_number.items()
            if invoice.is_overdue(now_epoch)
        )

    def of_customer(self, customer_reference: str) -> list[str]:
        """List the invoice numbers of one customer."""
        return sorted(
            number
            for number, invoice in self._by_number.items()
            if invoice.customer_reference == customer_reference
        )

    def open_total_cents(self) -> int:
        """Report what the depot is still owed altogether."""
        return sum(invoice.open_cents() for invoice in self._by_number.values())

    def issued_notice_template(self) -> str:
        """Report the notice that goes out when an invoice is raised."""
        return depot.billing.services.invoice_service.ISSUED_TEMPLATE
