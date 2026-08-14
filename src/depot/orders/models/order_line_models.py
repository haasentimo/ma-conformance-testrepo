"""The single parcels an order consists of.

One line is one physical parcel: what is in it, what it weighs, what it costs.
The weight decides the price band, so it is checked here and not left to the
counter software.
"""

import sqlalchemy.orm

import depot.core.errors

MAX_LINE_WEIGHT_GRAMS: int = 31500
MAX_QUANTITY: int = 20


class OrderLine:
    """One parcel of an order."""

    __tablename__ = "order_line"

    id: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(primary_key=True)
    reference: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(unique=True)
    order_reference: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column()
    description: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column()
    weight_grams: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column()
    quantity: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(default=1)
    unit_price_cents: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        default=0
    )
    fragile: sqlalchemy.orm.Mapped[bool] = sqlalchemy.orm.mapped_column(default=False)

    def check(self) -> None:
        """Raise unless the parcel is one the depot may accept."""
        if not 0 < self.weight_grams <= MAX_LINE_WEIGHT_GRAMS:
            raise depot.core.errors.ValidationError(
                "weight_grams", f"must be between 1 and {MAX_LINE_WEIGHT_GRAMS}"
            )
        if not 0 < self.quantity <= MAX_QUANTITY:
            raise depot.core.errors.ValidationError(
                "quantity", f"must be between 1 and {MAX_QUANTITY}"
            )
        if not self.description.strip():
            raise depot.core.errors.ValidationError(
                "description", "the customs form needs a description"
            )

    def total_cents(self) -> int:
        """Report what the whole line costs."""
        return self.unit_price_cents * self.quantity

    def total_weight_grams(self) -> int:
        """Report what the whole line weighs."""
        return self.weight_grams * self.quantity

    def needs_two_hands(self) -> bool:
        """Report whether a single parcel of this line is a two-person lift."""
        return self.weight_grams > 20000 or self.fragile
