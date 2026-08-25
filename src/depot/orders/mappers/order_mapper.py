"""Translation between order headers and the shapes the API exchanges."""

import depot.core.errors
import depot.orders.api.routes
import depot.orders.models.order_models

ZONE_LENGTH_LIMIT: int = 8


def to_payload(order: depot.orders.models.order_models.Order) -> dict[str, object]:
    """Build the body an order endpoint returns for one header."""
    return {
        "reference": order.reference,
        "customer": order.customer_reference,
        "zone": order.destination_zone,
        "status": order.status,
        "placed_at": order.placed_at,
        "parcels": order.line_count,
        "total_cents": order.total_cents,
        "open": order.is_open(),
    }


def to_board_line(order: depot.orders.models.order_models.Order) -> str:
    """Build the single line the dispatch board prints for an order."""
    return f"{order.reference}  {order.destination_zone}  {order.line_count} pcs"


def check_zone(zone: str) -> str:
    """Return a destination zone in the form the depot files it under."""
    cleaned = zone.strip().upper()
    if not cleaned:
        raise depot.core.errors.ValidationError("zone", "a shipment needs a destination")
    if len(cleaned) > ZONE_LENGTH_LIMIT:
        raise depot.core.errors.ValidationError(
            "zone", f"must not be longer than {ZONE_LENGTH_LIMIT} characters"
        )
    return cleaned


def next_states(order: depot.orders.models.order_models.Order) -> list[str]:
    """List the states the counter may still move an order to."""
    return sorted(depot.orders.models.order_models.STATUS_FLOW.get(order.status, ()))


def to_error_payload(error: depot.core.errors.DepotError) -> dict[str, object]:
    """Build the body the order endpoints return for a depot error."""
    return {
        "error": type(error).__name__,
        "status": depot.orders.api.routes.status_for(error),
    }
