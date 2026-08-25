"""Customer use cases of the depot counter.

Everything a clerk can do to a customer account goes through here: registering
someone at the counter, confirming their delivery address, blocking an account
after a dispute. The service also files the signed hand-over forms, which is
why it holds the document store.
"""

import depot.core.adapters.internal.session
import depot.core.adapters.storage
import depot.core.ports
import depot.identity.repository.customer_repo

WELCOME_TEMPLATE: str = "customer.welcome"
VERIFIED_TEMPLATE: str = "customer.verified"
BLOCKED_TEMPLATE: str = "customer.blocked"


class CustomerService:
    """Drives the customer side of the counter."""

    def __init__(
        self,
        customers: depot.identity.repository.customer_repo.CustomerRepository,
        notifier: depot.core.ports.NotificationSender,
        documents: depot.core.adapters.storage.ParcelDocumentStore,
    ) -> None:
        self.customers: depot.identity.repository.customer_repo.CustomerRepository = (
            customers
        )
        self.notifier: depot.core.ports.NotificationSender = notifier
        self.documents: depot.core.adapters.storage.ParcelDocumentStore = documents

    def register(self, email: str, display_name: str, phone: str) -> str:
        """Register a customer at the counter and return their reference.

        Registering the same address twice is what happens when a customer
        forgets they already have an account, so it is not an error: the
        existing reference is handed back and no welcome notice goes out.
        """
        existing = self.customers.find_by_email(email)
        if existing is not None:
            return existing.reference
        reference = self.customers.create(email, display_name, phone)
        self.notifier.send(
            email,
            WELCOME_TEMPLATE,
            {"display_name": display_name, "reference": reference},
        )
        return reference

    def fetch(
        self, reference: str
    ) -> depot.identity.repository.customer_repo.CustomerRecord | None:
        """Return the record filed under a reference, or None."""
        return self.customers.get(reference)

    def confirm_address(self, reference: str, confirmed_at: float) -> bool:
        """Confirm a delivery address and report whether anything changed."""
        customer = self.customers.get(reference)
        if customer is None:
            return False
        if not self.customers.verify(reference, confirmed_at):
            return False
        self.notifier.send(customer.email, VERIFIED_TEMPLATE, {"reference": reference})
        return True

    def block(self, reference: str, reason: str) -> bool:
        """Block an account after a counter dispute and tell the customer."""
        customer = self.customers.get(reference)
        if customer is None:
            return False
        self.customers.block(reference, reason)
        self.notifier.send(
            customer.email,
            BLOCKED_TEMPLATE,
            {"reference": reference, "reason": reason},
        )
        return True

    def file_handover_form(self, reference: str, day: str, form: bytes) -> str:
        """Store the signed hand-over form and return its storage key."""
        return self.documents.put_manifest(reference, day, form)

    def handover_form(self, reference: str, day: str) -> bytes | None:
        """Return a filed hand-over form, or None if none was ever stored."""
        return self.documents.read(self.documents.key_for(reference, day, "manifest"))

    def blocked_today(self) -> list[str]:
        """List the references the counter must refuse."""
        return self.customers.blocked_references()

    def purge_documents(
        self, session: depot.core.adapters.internal.session.Session
    ) -> int:
        """Drop the filed forms of closed accounts through the session."""
        session.execute("delete from customer_document where account_closed")
        return session.commit()
