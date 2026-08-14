"""Order use cases of the depot counter.

Placing an order is the one operation that crosses a context boundary: the
depot refuses a shipment from a customer who may not collect, so the customer
side is asked before anything is written. The dispatch manifest is filed
through the adapter facade.
"""

import depot.core.adapters.storage
import depot.core.ports
import depot.identity.services.customer_service
import depot.orders.repository.order_repo

PLACED_TEMPLATE: str = "order.placed"
CANCELLED_TEMPLATE: str = "order.cancelled"


class OrderService:
    """Drives the order side of the counter."""

    def __init__(
        self,
        orders: depot.orders.repository.order_repo.OrderRepository,
        customers: depot.identity.services.customer_service.CustomerService,
        notifier: depot.core.ports.NotificationSender,
        documents: depot.core.adapters.storage.ParcelDocumentStore,
    ) -> None:
        self.orders: depot.orders.repository.order_repo.OrderRepository = orders
        self.customers: depot.identity.services.customer_service.CustomerService = (
            customers
        )
        self.notifier: depot.core.ports.NotificationSender = notifier
        self.documents: depot.core.adapters.storage.ParcelDocumentStore = documents

    def open_order(self, customer_reference: str, destination_zone: str) -> str:
        """Open a draft order for a customer the depot still serves.

        An unknown or blocked customer is answered with an empty reference
        rather than an error: the API turns that into the status code, and this
        layer has no business knowing which one.
        """
        customer = self.customers.fetch(customer_reference)
        if customer is None or not customer.may_collect():
            return ""
        return self.orders.create(customer_reference, destination_zone)

    def fetch(
        self, reference: str
    ) -> depot.orders.repository.order_repo.OrderRecord | None:
        """Return the order filed under a reference, or None."""
        return self.orders.get(reference)

    def place(self, reference: str, placed_at: float) -> bool:
        """Hand an order over to dispatch and tell the customer."""
        order = self.orders.get(reference)
        if order is None or not self.orders.place(reference, placed_at):
            return False
        customer = self.customers.fetch(order.customer_reference)
        if customer is not None:
            self.notifier.send(
                customer.email,
                PLACED_TEMPLATE,
                {"reference": reference, "zone": order.destination_zone},
            )
        return True

    def cancel(self, reference: str) -> bool:
        """Withdraw an order and tell the customer."""
        order = self.orders.get(reference)
        if order is None or not self.orders.cancel(reference):
            return False
        customer = self.customers.fetch(order.customer_reference)
        if customer is not None:
            self.notifier.send(
                customer.email, CANCELLED_TEMPLATE, {"reference": reference}
            )
        return True

    def file_dispatch_manifest(
        self, reference: str, day: str, manifest: bytes
    ) -> str:
        """Store the manifest the van driver signs and return its key."""
        return self.documents.put_manifest(reference, day, manifest)

    def dispatch_manifest(self, reference: str, day: str) -> bytes | None:
        """Return a filed dispatch manifest, or None if there is none."""
        return self.documents.read(self.documents.key_for(reference, day, "manifest"))

    def open_orders_of(self, customer_reference: str) -> list[str]:
        """List the orders a customer still has running."""
        return self.orders.open_of_customer(customer_reference)
