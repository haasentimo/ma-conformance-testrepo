"""Error types raised throughout the depot.

Every context maps these onto its own transport format; the core itself never
catches them.
"""


class DepotError(Exception):
    """Base class of every error the depot raises on purpose."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message: str = message


class NotFoundError(DepotError):
    """A record was addressed that the depot does not hold."""

    def __init__(self, entity: str, reference: str) -> None:
        super().__init__(f"{entity} {reference!r} does not exist")
        self.entity: str = entity
        self.reference: str = reference


class ValidationError(DepotError):
    """Incoming data does not satisfy the rules of the depot."""

    def __init__(self, field: str, reason: str) -> None:
        super().__init__(f"field {field!r} is invalid: {reason}")
        self.field: str = field
        self.reason: str = reason


class ConflictError(DepotError):
    """The requested change collides with the state already stored.

    Raised when a parcel is handed in twice, an invoice is settled twice or a
    shipment is cancelled after it has left the depot.
    """


class PermissionDeniedError(DepotError):
    """The caller is known but may not perform this operation."""
