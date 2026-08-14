"""Payments that arrive for the invoices of the depot.

A payment carries the remittance reference the customer typed into their bank
form, and that is where most of the work is: the reference is often wrong, so
it is normalised here and matched by the query side.
"""

import depot.core.errors

METHOD_TRANSFER: str = "transfer"
METHOD_DIRECT_DEBIT: str = "direct_debit"
METHOD_CARD: str = "card"
METHOD_CASH: str = "cash"

KNOWN_METHODS: tuple[str, ...] = (
    METHOD_TRANSFER,
    METHOD_DIRECT_DEBIT,
    METHOD_CARD,
    METHOD_CASH,
)
REFERENCE_LENGTH: int = 14


class Payment:
    """One incoming payment as the bank statement reported it."""

    def __init__(
        self,
        reference: str,
        amount_cents: int,
        method: str,
        received_at: float,
        remittance_note: str = "",
    ) -> None:
        if method not in KNOWN_METHODS:
            raise depot.core.errors.ValidationError(
                "method", f"unknown payment method {method!r}"
            )
        if amount_cents <= 0:
            raise depot.core.errors.ValidationError(
                "amount_cents", "a payment has to move money"
            )
        self.reference: str = self.normalise(reference)
        self.amount_cents: int = amount_cents
        self.method: str = method
        self.received_at: float = received_at
        self.remittance_note: str = remittance_note

    def normalise(self, reference: str) -> str:
        """Strip the spacing a bank form leaves in a remittance reference."""
        return "".join(reference.split()).upper()

    def looks_matchable(self) -> bool:
        """Report whether the reference has the shape of an invoice number."""
        return len(self.reference) == REFERENCE_LENGTH and self.reference.isalnum()

    def is_reversible(self) -> bool:
        """Report whether the depot can still send this payment back."""
        return self.method in (METHOD_TRANSFER, METHOD_DIRECT_DEBIT)

    def printed_amount(self) -> str:
        """Format the amount the way the remittance advice prints it."""
        return f"{self.amount_cents // 100},{self.amount_cents % 100:02d}"


def cash_at_counter(amount_cents: int, received_at: float, slip: str) -> Payment:
    """Build the payment a clerk books when a customer pays at the counter."""
    return Payment(slip, amount_cents, METHOD_CASH, received_at, "counter")
