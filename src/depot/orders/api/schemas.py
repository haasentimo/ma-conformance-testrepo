"""Request and response shapes of the order endpoints.

The schemas check what a client sent before anything below the API sees it.
They know nothing about the records themselves — that translation is the
mappers' job.
"""

import depot.core.errors

MAX_LINES_PER_REQUEST: int = 50


class OrderDraft:
    """Body of a request that opens a new order."""

    def __init__(self, customer_reference: str, destination_zone: str) -> None:
        self.customer_reference: str = customer_reference
        self.destination_zone: str = destination_zone

    def validate(self) -> None:
        """Raise unless the body can open an order."""
        if not self.customer_reference.strip():
            raise depot.core.errors.ValidationError(
                "customer_reference", "must be named"
            )
        if not self.destination_zone.strip():
            raise depot.core.errors.ValidationError(
                "destination_zone", "must be named"
            )


class LineBatch:
    """Body of a request that adds parcels to an order."""

    def __init__(self, lines: list[dict[str, object]]) -> None:
        self.lines: list[dict[str, object]] = lines

    def validate(self) -> None:
        """Raise unless the batch is one the counter can take in one go."""
        if not self.lines:
            raise depot.core.errors.ValidationError(
                "lines", "a batch without a parcel changes nothing"
            )
        if len(self.lines) > MAX_LINES_PER_REQUEST:
            raise depot.core.errors.ValidationError(
                "lines", f"at most {MAX_LINES_PER_REQUEST} parcels per request"
            )


class QuoteRequest:
    """Body of a request that asks what a shipment would cost."""

    def __init__(self, zone: str, weight_grams: int, code: str = "") -> None:
        self.zone: str = zone
        self.weight_grams: int = weight_grams
        self.code: str = code

    def validate(self) -> None:
        """Raise unless the quote can be worked out."""
        if not self.zone.strip():
            raise depot.core.errors.ValidationError("zone", "must be named")
        if self.weight_grams <= 0:
            raise depot.core.errors.ValidationError(
                "weight_grams", "a parcel has to weigh something"
            )


def error_body(error: depot.core.errors.DepotError) -> dict[str, str]:
    """Build the body the API returns for an error the depot raised."""
    return {"error": type(error).__name__, "message": error.message}
