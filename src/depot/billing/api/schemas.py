"""Request and response shapes of the billing endpoints.

The schemas check what a client sent before anything below the API sees it.
They know nothing about the records themselves — that translation is the
mappers' job.
"""

import depot.core.errors

MAX_NOTICES_PER_BATCH: int = 500


class InvoiceDraft:
    """Body of a request that drafts an invoice for a shipment."""

    def __init__(
        self, customer_reference: str, order_reference: str, net_cents: int
    ) -> None:
        self.customer_reference: str = customer_reference
        self.order_reference: str = order_reference
        self.net_cents: int = net_cents

    def validate(self) -> None:
        """Raise unless the body can draft an invoice."""
        if not self.customer_reference.strip():
            raise depot.core.errors.ValidationError(
                "customer_reference", "must be named"
            )
        if not self.order_reference.strip():
            raise depot.core.errors.ValidationError("order_reference", "must be named")
        if self.net_cents <= 0:
            raise depot.core.errors.ValidationError(
                "net_cents", "an invoice needs an amount"
            )


class SettlementNotice:
    """Body of a request that books money against an invoice."""

    def __init__(self, number: str, amount_cents: int) -> None:
        self.number: str = number
        self.amount_cents: int = amount_cents

    def validate(self) -> None:
        """Raise unless the notice moves money against a named invoice."""
        if not self.number.strip():
            raise depot.core.errors.ValidationError("number", "must be named")
        if self.amount_cents <= 0:
            raise depot.core.errors.ValidationError(
                "amount_cents", "a settlement has to move money"
            )


class StatementBatch:
    """Body of a request that hands in a bank statement."""

    def __init__(self, notices: list[dict[str, object]]) -> None:
        self.notices: list[dict[str, object]] = notices

    def validate(self) -> None:
        """Raise unless the batch is one the billing run can take in one go."""
        if not self.notices:
            raise depot.core.errors.ValidationError(
                "notices", "an empty statement changes nothing"
            )
        if len(self.notices) > MAX_NOTICES_PER_BATCH:
            raise depot.core.errors.ValidationError(
                "notices", f"at most {MAX_NOTICES_PER_BATCH} notices per request"
            )


def error_body(error: depot.core.errors.DepotError) -> dict[str, str]:
    """Build the body the API returns for an error the depot raised."""
    return {"error": type(error).__name__, "message": error.message}
