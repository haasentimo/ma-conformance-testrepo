"""Storage of the customer records.

The repository owns the reference a customer is filed under. It asks the
id generator for one before the first write so that the collection slip can be
printed in the same counter interaction.
"""

import depot.core.ports
import depot.identity.models.customer_models

CustomerRecord = depot.identity.models.customer_models.Customer
"""The record type this repository hands out.

The layers above the repository do not reach into the models package, so they
name the type through here.
"""


class CustomerRepository:
    """Reads and writes customer records."""

    def __init__(self, ids: depot.core.ports.IdGenerator) -> None:
        self.ids: depot.core.ports.IdGenerator = ids
        self._by_reference: dict[
            str, depot.identity.models.customer_models.Customer
        ] = {}

    def create(self, email: str, display_name: str, phone: str) -> str:
        """File a new customer and return the reference it was filed under."""
        customer = depot.identity.models.customer_models.Customer()
        customer.email = email
        customer.display_name = display_name
        customer.phone = phone
        reference = self.ids.new_id("cust")
        customer.reference = reference
        self._by_reference[reference] = customer
        return reference

    def verify(self, reference: str, confirmed_at: float) -> bool:
        """Record an address confirmation; report whether anything changed."""
        customer = self._by_reference.get(reference)
        if customer is None or customer.may_collect():
            return False
        customer.mark_verified(confirmed_at)
        return True

    def get(
        self, reference: str
    ) -> depot.identity.models.customer_models.Customer | None:
        """Return the customer filed under a reference, or None."""
        return self._by_reference.get(reference)

    def find_by_email(
        self, email: str
    ) -> depot.identity.models.customer_models.Customer | None:
        """Return the customer registered with an address, or None."""
        for customer in self._by_reference.values():
            if customer.email == email:
                return customer
        return None

    def block(self, reference: str, reason: str) -> bool:
        """Block a customer and report whether the reference was known.

        Blocking is the last step of a counter dispute. Everything that follows
        from it — withdrawing the open collection slips, telling the customer —
        happens above this layer.
        """
        customer = self._by_reference.get(reference)
        if customer is None:
            return False
        customer.block(reason)
        return True

    def blocked_references(self) -> list[str]:
        """List the references the counter must refuse today."""
        return sorted(
            reference
            for reference, customer in self._by_reference.items()
            if customer.blocked_reason is not None
        )

    def count(self) -> int:
        """Report how many customers are on file."""
        return len(self._by_reference)
