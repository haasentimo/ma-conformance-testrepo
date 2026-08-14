"""Shipment orders placed at the depot counter.

An order is the header: who is sending, where it goes, what it costs and how
far it has got. The parcels themselves are the lines. The header carries the
counted totals of its lines because the dispatch board reads them on every
refresh and the join was too slow for that.
"""

import sqlalchemy.orm

import depot.core.errors

STATUS_DRAFT: str = "draft"
STATUS_PLACED: str = "placed"
STATUS_DISPATCHED: str = "dispatched"
STATUS_CANCELLED: str = "cancelled"

STATUS_FLOW: dict[str, tuple[str, ...]] = {
    STATUS_DRAFT: (STATUS_PLACED, STATUS_CANCELLED),
    STATUS_PLACED: (STATUS_DISPATCHED, STATUS_CANCELLED),
    STATUS_DISPATCHED: (),
    STATUS_CANCELLED: (),
}


class Order:
    """A shipment order and everything the counter decided about it."""

    __tablename__ = "shipment_order"

    id: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(primary_key=True)
    reference: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(unique=True)
    customer_reference: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column()
    destination_zone: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column()
    status: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        default=STATUS_DRAFT
    )
    placed_at: sqlalchemy.orm.Mapped[float | None] = sqlalchemy.orm.mapped_column(
        default=None
    )
    line_count: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(default=0)
    total_cents: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(default=0)

    def move_to(self, status: str) -> None:
        """Advance the order, refusing a step the flow does not allow."""
        allowed = STATUS_FLOW.get(self.status)
        if allowed is None:
            raise depot.core.errors.ValidationError(
                "status", f"unknown status {self.status!r}"
            )
        if status not in allowed:
            raise depot.core.errors.ConflictError(
                f"an order in {self.status!r} cannot move to {status!r}"
            )
        self.status = status

    def place(self, placed_at: float) -> None:
        """Hand the order over to dispatch."""
        if self.line_count <= 0:
            raise depot.core.errors.ValidationError(
                "line_count", "an order without a parcel cannot be placed"
            )
        self.move_to(STATUS_PLACED)
        self.placed_at = placed_at

    def cancel(self) -> None:
        """Withdraw the order before it has left the depot."""
        self.move_to(STATUS_CANCELLED)

    def is_open(self) -> bool:
        """Report whether the depot still owes the customer something."""
        return self.status in (STATUS_DRAFT, STATUS_PLACED)

    def add_line_total(self, amount_cents: int) -> None:
        """Book one more parcel and its share of the price onto the header."""
        if amount_cents < 0:
            raise depot.core.errors.ValidationError(
                "amount_cents", "a line cannot be worth less than nothing"
            )
        self.line_count += 1
        self.total_cents += amount_cents
