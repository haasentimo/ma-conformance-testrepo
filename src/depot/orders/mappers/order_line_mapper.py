"""Translation between order lines and the shapes the API exchanges."""

import depot.core.errors
import depot.orders.models.order_line_models

REQUIRED_FIELDS: frozenset[str] = frozenset(
    {"description", "weight_grams", "quantity"}
)


def to_payload(
    line: depot.orders.models.order_line_models.OrderLine,
) -> dict[str, str]:
    """Build the body a line endpoint returns for one parcel."""
    return {
        "reference": line.reference,
        "order": line.order_reference,
        "description": line.description,
        "weight_grams": line.weight_grams,
        "quantity": line.quantity,
        "unit_price_cents": line.unit_price_cents,
        "total_cents": line.total_cents(),
        "fragile": line.fragile,
        "two_hands": line.needs_two_hands(),
    }


def to_shelf_label(
    line: depot.orders.models.order_line_models.OrderLine,
) -> str:
    """Build the text the shelf label carries for one parcel."""
    marks = " ".join(
        mark
        for mark, present in (("FRAGILE", line.fragile), ("HEAVY", line.needs_two_hands()))
        if present
    )
    return f"{line.reference} {line.description[:24]} {marks}".rstrip()


def normalise_request(lines: list[dict[str, object]]) -> list[dict[str, object]]:
    """Check the parcels of an incoming order and return them in canonical form.

    A client that leaves out a field expects the depot to know what it meant,
    and it does not — a missing weight is refused here rather than guessed, so
    that no parcel reaches the shelf with a made-up price band.
    """
    if not lines:
        raise depot.core.errors.ValidationError(
            "lines", "an order needs at least one parcel"
        )
    canonical: list[dict[str, object]] = []
    for position, line in enumerate(lines):
        missing = sorted(REQUIRED_FIELDS - set(line))
        if missing:
            raise depot.core.errors.ValidationError(
                f"lines[{position}].{missing[0]}", "is required"
            )
        canonical.append(
            {
                "description": str(line["description"]).strip(),
                "weight_grams": int(str(line["weight_grams"])),
                "quantity": int(str(line["quantity"])),
                "fragile": bool(line.get("fragile", False)),
            }
        )
    return canonical
