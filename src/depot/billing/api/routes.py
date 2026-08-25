"""Endpoints of the billing context.

The handlers ask the service for the work, hand what comes back to a mapper and
turn a depot error into a status code. Storage is none of their business — a
handler never reaches past the service.
"""

import depot.core.errors
import depot.billing.mappers.invoice_mapper
import depot.billing.mappers.payment_mapper
import depot.billing.repository.invoice_repo
import depot.billing.services.invoice_service

STATUS_BY_ERROR: dict[str, int] = {
    "NotFoundError": 404,
    "ValidationError": 422,
    "ConflictError": 409,
    "PermissionDeniedError": 403,
}
STATUS_UNEXPECTED: int = 500


class InvoiceRoutes:
    """The invoice endpoints of the billing API."""

    def __init__(
        self, invoices: depot.billing.services.invoice_service.InvoiceService
    ) -> None:
        self.invoices: depot.billing.services.invoice_service.InvoiceService = invoices

    def post_invoice(
        self, customer_reference: str, order_reference: str, net_cents: int
    ) -> dict[str, object]:
        """Draft an invoice for a shipment and return what was created."""
        number = self.invoices.raise_invoice(
            customer_reference, order_reference, net_cents
        )
        if not number:
            raise depot.core.errors.PermissionDeniedError(
                f"customer {customer_reference!r} may not be invoiced"
            )
        return self.get_invoice(number)

    def get_invoice(self, number: str) -> dict[str, object]:
        """Return one invoice."""
        clean = depot.billing.mappers.invoice_mapper.check_number(number)
        invoice = self.invoices.fetch(clean)
        if invoice is None:
            raise depot.core.errors.NotFoundError("invoice", clean)
        payload = depot.billing.mappers.invoice_mapper.to_payload(invoice)
        payload["settled"] = depot.billing.mappers.invoice_mapper.is_settled(invoice)
        return payload

    def post_issue(self, number: str, issued_at: float) -> dict[str, object]:
        """Raise an invoice and send it out."""
        clean = depot.billing.mappers.invoice_mapper.check_number(number)
        if not self.invoices.issue(clean, issued_at):
            raise depot.core.errors.ConflictError(
                f"invoice {clean!r} could not be issued"
            )
        return self.get_invoice(clean)

    def get_document_header(self, number: str) -> dict[str, str]:
        """Return the header line printed on the invoice document."""
        clean = depot.billing.mappers.invoice_mapper.check_number(number)
        invoice = self.invoices.fetch(clean)
        if invoice is None:
            raise depot.core.errors.NotFoundError("invoice", clean)
        return {
            "header": depot.billing.mappers.invoice_mapper.to_document_header(invoice)
        }

    def get_invoices_of_customer(
        self, customer_reference: str
    ) -> dict[str, object]:
        """List the invoices of one customer."""
        return {"numbers": self.invoices.invoices_of(customer_reference)}

    def get_open_total(
        self, invoices: depot.billing.repository.invoice_repo.InvoiceRepository
    ) -> dict[str, int]:
        """Return what the depot is still owed, straight from storage."""
        return {"open_cents": invoices.open_total_cents()}


class PaymentRoutes:
    """The payment endpoints the bank interface posts to."""

    def __init__(
        self, invoices: depot.billing.services.invoice_service.InvoiceService
    ) -> None:
        self.invoices: depot.billing.services.invoice_service.InvoiceService = invoices

    def post_statement(
        self, notices: list[dict[str, object]]
    ) -> dict[str, object]:
        """Take in a bank statement and report what was booked."""
        accepted: list[dict[str, object]] = [
            depot.billing.mappers.payment_mapper.normalise_notice(notice)
            for notice in notices
        ]
        booked = 0
        for notice in accepted:
            number = str(notice["reference"])
            if self.invoices.fetch(number) is None:
                continue
            self.invoices.settle(number, int(str(notice["amount_cents"])))
            booked += 1
        return {"accepted": len(accepted), "booked": booked, "notices": accepted}

    def post_settlement(self, number: str, amount_cents: int) -> dict[str, object]:
        """Book one payment against an invoice by hand."""
        if self.invoices.fetch(number) is None:
            raise depot.core.errors.NotFoundError("invoice", number)
        return {"number": number, "open_cents": self.invoices.settle(number, amount_cents)}


def status_for(error: depot.core.errors.DepotError) -> int:
    """Map a depot error onto the status code the API answers with."""
    return STATUS_BY_ERROR.get(type(error).__name__, STATUS_UNEXPECTED)
