"""Invoice use cases of the depot.

Raising an invoice crosses a context boundary: the depot only bills a customer
it still serves, so the customer side is asked before anything is written. The
issued document itself is filed through the adapter facade.
"""

import depot.core.adapters.internal.session
import depot.core.adapters.storage
import depot.core.ports
import depot.identity.services.customer_service
import depot.billing.repository.invoice_repo

ISSUED_TEMPLATE: str = "invoice.issued"
SETTLED_TEMPLATE: str = "invoice.settled"


class InvoiceService:
    """Drives the invoicing side of the depot."""

    def __init__(
        self,
        invoices: depot.billing.repository.invoice_repo.InvoiceRepository,
        customers: depot.identity.services.customer_service.CustomerService,
        notifier: depot.core.ports.NotificationSender,
        documents: depot.core.adapters.storage.ParcelDocumentStore,
    ) -> None:
        self.invoices: depot.billing.repository.invoice_repo.InvoiceRepository = (
            invoices
        )
        self.customers: depot.identity.services.customer_service.CustomerService = (
            customers
        )
        self.notifier: depot.core.ports.NotificationSender = notifier
        self.documents: depot.core.adapters.storage.ParcelDocumentStore = documents

    def raise_invoice(
        self, customer_reference: str, order_reference: str, net_cents: int
    ) -> str:
        """Draft an invoice for a shipment the depot has carried out.

        A customer the depot no longer serves is answered with an empty number
        rather than an error: the API turns that into the status code, and this
        layer has no business knowing which one.
        """
        customer = self.customers.fetch(customer_reference)
        if customer is None or customer.blocked_reason is not None:
            return ""
        return self.invoices.create(customer_reference, order_reference, net_cents)

    def fetch(
        self, number: str
    ) -> depot.billing.repository.invoice_repo.InvoiceRecord | None:
        """Return the invoice filed under a number, or None."""
        return self.invoices.get(number)

    def issue(self, number: str, issued_at: float) -> bool:
        """Raise an invoice and send it to the customer."""
        invoice = self.invoices.get(number)
        if invoice is None or not self.invoices.issue(number, issued_at):
            return False
        customer = self.customers.fetch(invoice.customer_reference)
        if customer is not None:
            self.notifier.send(
                customer.email,
                ISSUED_TEMPLATE,
                {"number": number, "amount": str(invoice.gross_cents())},
            )
        return True

    def settle(self, number: str, amount_cents: int) -> int:
        """Book money against an invoice and tell the customer when it is done."""
        invoice = self.invoices.get(number)
        if invoice is None:
            return 0
        open_cents = self.invoices.settle(number, amount_cents)
        if open_cents == 0:
            customer = self.customers.fetch(invoice.customer_reference)
            if customer is not None:
                self.notifier.send(
                    customer.email, SETTLED_TEMPLATE, {"number": number}
                )
        return open_cents

    def file_document(self, number: str, day: str, document: bytes) -> str:
        """Store the issued invoice document and return its storage key."""
        return self.documents.put_manifest(number, day, document)

    def document(self, number: str, day: str) -> bytes | None:
        """Return a filed invoice document, or None if there is none."""
        return self.documents.read(self.documents.key_for(number, day, "manifest"))

    def invoices_of(self, customer_reference: str) -> list[str]:
        """List the invoice numbers of one customer."""
        return self.invoices.of_customer(customer_reference)

    def purge_documents(
        self, session: depot.core.adapters.internal.session.Session
    ) -> int:
        """Drop the documents of settled invoices through the session."""
        session.execute("delete from invoice_document where invoice_settled")
        return session.commit()
