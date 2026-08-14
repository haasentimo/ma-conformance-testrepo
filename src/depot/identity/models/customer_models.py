"""Customer records of the depot.

A customer is whoever may hand in or collect a parcel at the counter. The
record carries the contact details the notification templates fill in and the
two flags the counter checks before it releases anything.
"""

import sqlalchemy.orm

import depot.core.errors

MIN_DISPLAY_NAME_LENGTH: int = 2


class Customer:
    """A customer account that may hand in and collect parcels."""

    __tablename__ = "customer"

    id: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(primary_key=True)
    reference: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(unique=True)
    email: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(unique=True)
    display_name: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column()
    phone: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column()
    verified_at: sqlalchemy.orm.Mapped[float | None] = sqlalchemy.orm.mapped_column(
        default=None
    )
    blocked_reason: sqlalchemy.orm.Mapped[str | None] = sqlalchemy.orm.mapped_column(
        default=None
    )

    def mark_verified(self, verified_at: float) -> None:
        """Record when the customer confirmed their delivery address."""
        if self.blocked_reason is not None:
            raise depot.core.errors.ConflictError(
                "a blocked customer cannot be verified"
            )
        self.verified_at = verified_at

    def block(self, reason: str) -> None:
        """Refuse further hand-ins and collections for this customer."""
        if not reason:
            raise depot.core.errors.ValidationError("reason", "must not be empty")
        self.blocked_reason = reason

    def unblock(self) -> None:
        """Lift a block; an account that was never blocked stays as it is."""
        self.blocked_reason = None

    def rename(self, display_name: str) -> None:
        """Change the name printed on the collection slip."""
        if len(display_name) < MIN_DISPLAY_NAME_LENGTH:
            raise depot.core.errors.ValidationError(
                "display_name", f"needs at least {MIN_DISPLAY_NAME_LENGTH} characters"
            )
        self.display_name = display_name

    def may_collect(self) -> bool:
        """Report whether the counter may release a parcel to this customer."""
        return self.verified_at is not None and self.blocked_reason is None
