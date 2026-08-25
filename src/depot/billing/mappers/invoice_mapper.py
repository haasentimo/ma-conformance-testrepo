"""Translation between invoices and the shapes the API exchanges."""

import depot.core.errors
import depot.billing.api.routes
import depot.billing.models.invoice_models

NUMBER_LENGTH: int = 14


def to_payload(
    invoice: depot.billing.models.invoice_models.Invoice,
) -> dict[str, object]:
    """Build the body an invoice endpoint returns for one invoice."""
    return {
        "number": invoice.number,
        "customer": invoice.customer_reference,
        "order": invoice.order_reference,
        "status": invoice.status,
        "net_cents": invoice.net_cents,
        "vat_cents": invoice.vat_cents(),
        "gross_cents": invoice.gross_cents(),
        "open_cents": invoice.open_cents(),
        "issued_at": invoice.issued_at,
        "due_at": invoice.due_at(),
        "reminders_sent": invoice.reminders_sent,
    }


def to_document_header(
    invoice: depot.billing.models.invoice_models.Invoice,
) -> str:
    """Build the header line printed at the top of the invoice document."""
    return (
        f"Invoice {invoice.number} · shipment {invoice.order_reference} · "
        f"{invoice.gross_cents() // 100},{invoice.gross_cents() % 100:02d}"
    )


def check_number(number: str) -> str:
    """Return an invoice number in the form the depot files it under."""
    cleaned = "".join(number.split()).upper()
    if not cleaned:
        raise depot.core.errors.ValidationError("number", "must be given")
    if len(cleaned) > NUMBER_LENGTH:
        raise depot.core.errors.ValidationError(
            "number", f"must not be longer than {NUMBER_LENGTH} characters"
        )
    return cleaned


def is_settled(invoice: depot.billing.models.invoice_models.Invoice) -> bool:
    """Report whether an invoice needs nothing further from the customer."""
    return invoice.status == depot.billing.models.invoice_models.STATUS_SETTLED


def to_error_payload(error: depot.core.errors.DepotError) -> dict[str, object]:
    """Build the body the invoice endpoints return for a depot error."""
    return {
        "error": type(error).__name__,
        "status": depot.billing.api.routes.status_for(error),
    }
