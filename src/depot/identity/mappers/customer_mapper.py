"""Translation between customer records and the shapes the API exchanges."""

import depot.core.errors
import depot.identity.models.customer_models

WRITABLE_FIELDS: frozenset[str] = frozenset({"display_name", "phone"})


def to_payload(
    customer: depot.identity.models.customer_models.Customer,
) -> dict[str, object]:
    """Build the body a customer endpoint returns for one record."""
    return {
        "reference": customer.reference,
        "email": customer.email,
        "display_name": customer.display_name,
        "phone": customer.phone,
        "verified": customer.verified_at is not None,
        "blocked": customer.blocked_reason is not None,
        "may_collect": customer.may_collect(),
    }


def to_slip_line(
    customer: depot.identity.models.customer_models.Customer,
) -> str:
    """Build the line the collection slip carries under the barcode."""
    return f"{customer.reference}  {customer.display_name}"


def apply_changes(
    customer: depot.identity.models.customer_models.Customer,
    changes: dict[str, str],
) -> int:
    """Write the writable fields of a change request and count what moved.

    Anything outside the writable set is refused rather than ignored: a client
    that sends ``email`` expects the address to change, and silently dropping
    it would leave the counter and the customer with different records.
    """
    unknown = sorted(set(changes) - WRITABLE_FIELDS)
    if unknown:
        raise depot.core.errors.ValidationError(
            unknown[0], "is not writable through this endpoint"
        )
    moved = 0
    if "display_name" in changes:
        customer.rename(changes["display_name"])
        moved += 1
    if "phone" in changes:
        customer.phone = changes["phone"]
        moved += 1
    return moved
