"""Translation between payments and the shapes the API exchanges."""

import depot.core.errors
import depot.billing.models.payment_models

REQUIRED_FIELDS: frozenset[str] = frozenset({"reference", "amount_cents", "method"})


def to_payload(
    payment: depot.billing.models.payment_models.Payment,
) -> dict[str, object]:
    """Build the body a payment endpoint returns for one payment."""
    return {
        "reference": payment.reference,
        "amount_cents": payment.amount_cents,
        "printed_amount": payment.printed_amount(),
        "method": payment.method,
        "received_at": payment.received_at,
        "matchable": payment.looks_matchable(),
        "reversible": payment.is_reversible(),
    }


def to_remittance_line(
    payment: depot.billing.models.payment_models.Payment,
) -> str:
    """Build the line the remittance advice carries for one payment."""
    return f"{payment.reference}  {payment.printed_amount()}  {payment.method}"


def normalise_notice(notice: dict[str, object]) -> dict[str, object]:
    """Check an incoming payment notice and return it in canonical form.

    A notice that names no method is refused rather than guessed: booking a
    card payment as a transfer would make it look reversible, and the depot
    would promise a customer money back it cannot send.
    """
    missing = sorted(REQUIRED_FIELDS - set(notice))
    if missing:
        raise depot.core.errors.ValidationError(missing[0], "is required")
    method = str(notice["method"]).strip().lower()
    if method not in depot.billing.models.payment_models.KNOWN_METHODS:
        raise depot.core.errors.ValidationError(
            "method", f"unknown payment method {method!r}"
        )
    return {
        "reference": "".join(str(notice["reference"]).split()).upper(),
        "amount_cents": int(str(notice["amount_cents"])),
        "method": method,
        "remittance_note": str(notice.get("remittance_note", "")).strip(),
    }
