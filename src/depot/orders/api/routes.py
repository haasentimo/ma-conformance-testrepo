"""Endpoints of the orders context.

The handlers ask the service for the work, hand what comes back to a mapper and
turn a depot error into a status code. Storage is none of their business — a
handler never reaches past the service.
"""

import depot.core.errors
import depot.orders.mappers.order_line_mapper
import depot.orders.mappers.order_mapper
import depot.orders.repository.order_repo
import depot.orders.services.order_service

STATUS_BY_ERROR: dict[str, int] = {
    "NotFoundError": 404,
    "ValidationError": 422,
    "ConflictError": 409,
    "PermissionDeniedError": 403,
}
STATUS_UNEXPECTED: int = 500


class OrderRoutes:
    """The order endpoints of the counter API."""

    def __init__(
        self, orders: depot.orders.services.order_service.OrderService
    ) -> None:
        self.orders: depot.orders.services.order_service.OrderService = orders

    def post_order(
        self, customer_reference: str, destination_zone: str
    ) -> dict[str, object]:
        """Open a draft order and return the header that was created."""
        zone = depot.orders.mappers.order_mapper.check_zone(destination_zone)
        reference = self.orders.open_order(customer_reference, zone)
        if not reference:
            raise depot.core.errors.PermissionDeniedError(
                f"customer {customer_reference!r} may not place shipments"
            )
        return self.get_order(reference)

    def get_order(self, reference: str) -> dict[str, object]:
        """Return one order header."""
        order = self.orders.fetch(reference)
        if order is None:
            raise depot.core.errors.NotFoundError("order", reference)
        payload = depot.orders.mappers.order_mapper.to_payload(order)
        payload["next_states"] = depot.orders.mappers.order_mapper.next_states(order)
        return payload

    def post_lines(
        self, reference: str, lines: list[dict[str, object]]
    ) -> dict[str, object]:
        """Take in the parcels of an order and return what was accepted."""
        if self.orders.fetch(reference) is None:
            raise depot.core.errors.NotFoundError("order", reference)
        accepted = depot.orders.mappers.order_line_mapper.normalise_request(lines)
        return {"reference": reference, "accepted": len(accepted), "lines": accepted}

    def post_placement(self, reference: str, placed_at: float) -> dict[str, object]:
        """Hand an order over to dispatch."""
        if not self.orders.place(reference, placed_at):
            raise depot.core.errors.ConflictError(
                f"order {reference!r} could not be placed"
            )
        return self.get_order(reference)

    def delete_order(self, reference: str) -> dict[str, object]:
        """Withdraw an order before it has left the depot."""
        if not self.orders.cancel(reference):
            raise depot.core.errors.ConflictError(
                f"order {reference!r} could not be cancelled"
            )
        return self.get_order(reference)

    def get_board(self, reference: str) -> dict[str, str]:
        """Return the single line the dispatch board prints for an order."""
        order = self.orders.fetch(reference)
        if order is None:
            raise depot.core.errors.NotFoundError("order", reference)
        return {"line": depot.orders.mappers.order_mapper.to_board_line(order)}

    def get_open_of_customer(self, customer_reference: str) -> dict[str, object]:
        """List the orders a customer still has running."""
        return {"references": self.orders.open_orders_of(customer_reference)}

    def get_order_count(
        self, orders: depot.orders.repository.order_repo.OrderRepository
    ) -> dict[str, int]:
        """Return how many orders are on file, straight from storage."""
        return {"count": orders.count()}


def status_for(error: depot.core.errors.DepotError) -> int:
    """Map a depot error onto the status code the API answers with."""
    return STATUS_BY_ERROR.get(type(error).__name__, STATUS_UNEXPECTED)
