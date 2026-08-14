"""Endpoints of the identity context.

The handlers do three things and nothing else: ask the service for the work,
hand what comes back to a mapper, and turn a depot error into a status code.
Storage is none of their business — a handler never reaches past the service.
"""

import depot.core.errors
import depot.identity.mappers.customer_mapper
import depot.identity.mappers.role_mapper
import depot.identity.services.customer_service

STATUS_BY_ERROR: dict[str, int] = {
    "NotFoundError": 404,
    "ValidationError": 422,
    "ConflictError": 409,
    "PermissionDeniedError": 403,
}
STATUS_UNEXPECTED: int = 500


class CustomerRoutes:
    """The customer endpoints of the counter API."""

    def __init__(
        self, customers: depot.identity.services.customer_service.CustomerService
    ) -> None:
        self.customers: depot.identity.services.customer_service.CustomerService = (
            customers
        )

    def post_customer(
        self, email: str, display_name: str, phone: str
    ) -> dict[str, object]:
        """Register a customer and return the record that was created."""
        reference = self.customers.register(email, display_name, phone)
        return self.get_customer(reference)

    def get_customer(self, reference: str) -> dict[str, object]:
        """Return one customer record."""
        customer = self.customers.fetch(reference)
        if customer is None:
            raise depot.core.errors.NotFoundError("customer", reference)
        return depot.identity.mappers.customer_mapper.to_payload(customer)

    def patch_customer(
        self, reference: str, changes: dict[str, str]
    ) -> dict[str, object]:
        """Change the contact details of a customer and return the record."""
        customer = self.customers.fetch(reference)
        if customer is None:
            raise depot.core.errors.NotFoundError("customer", reference)
        depot.identity.mappers.customer_mapper.apply_changes(customer, changes)
        return depot.identity.mappers.customer_mapper.to_payload(customer)

    def post_block(self, reference: str, reason: str) -> dict[str, object]:
        """Block a customer after a counter dispute."""
        if not self.customers.block(reference, reason):
            raise depot.core.errors.NotFoundError("customer", reference)
        return self.get_customer(reference)

    def post_address_confirmation(
        self, reference: str, confirmed_at: float
    ) -> dict[str, object]:
        """Confirm a delivery address."""
        if not self.customers.confirm_address(reference, confirmed_at):
            raise depot.core.errors.ConflictError(
                f"address of {reference!r} could not be confirmed"
            )
        return self.get_customer(reference)

    def get_blocked(self) -> dict[str, object]:
        """List the references the counter must refuse today."""
        return {"references": self.customers.blocked_today()}


class RoleRoutes:
    """The role endpoints the terminal reads when a clerk signs on."""

    def get_roles(self) -> list[dict[str, object]]:
        """List the roles a clerk can sign on with."""
        return depot.identity.mappers.role_mapper.catalogue()

    def get_role(self, name: str) -> dict[str, object]:
        """Return one role together with the permissions it grants."""
        role = depot.identity.mappers.role_mapper.from_name(name)
        return depot.identity.mappers.role_mapper.to_payload(role)


def status_for(error: depot.core.errors.DepotError) -> int:
    """Map a depot error onto the status code the API answers with."""
    return STATUS_BY_ERROR.get(type(error).__name__, STATUS_UNEXPECTED)
