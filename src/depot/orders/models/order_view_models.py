"""Read models behind the dispatch board.

The board on the wall of the sorting hall shows one row per order that has not
left yet: where it goes, how many parcels are on the shelf for it and how long
it has been waiting. The rows are rebuilt whenever an order changes state, and
the board reads nothing else — the hall has no time to wait for a join across
four tables while a van is at the ramp.
"""

import sqlalchemy.orm

import depot.core.errors

URGENT_AFTER_SECONDS: float = 4 * 60 * 60.0


class OrderBoardRow:
    """One line of the dispatch board in the sorting hall."""

    __tablename__ = "order_board_row"

    order_id: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        primary_key=True
    )
    reference: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(unique=True)
    destination_zone: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column()
    status: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column()
    parcels_on_shelf: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        default=0
    )
    waiting_since: sqlalchemy.orm.Mapped[float | None] = sqlalchemy.orm.mapped_column(
        default=None
    )

    def waited_seconds(self, now_epoch: float) -> float:
        """Report how long this order has been waiting for a van."""
        if self.waiting_since is None:
            return 0.0
        return max(0.0, now_epoch - self.waiting_since)

    def is_urgent(self, now_epoch: float) -> bool:
        """Report whether the board should show this row in red."""
        return self.waited_seconds(now_epoch) > URGENT_AFTER_SECONDS

    def sort_key(self, now_epoch: float) -> tuple[int, float]:
        """Build the key the board sorts by: urgent first, longest waiting first."""
        return (0 if self.is_urgent(now_epoch) else 1, -self.waited_seconds(now_epoch))

    def label(self) -> str:
        """Build the text the board prints in the destination column."""
        if not self.destination_zone:
            raise depot.core.errors.ValidationError(
                "destination_zone", "a board row without a zone cannot be shown"
            )
        return f"{self.destination_zone} · {self.parcels_on_shelf} pcs"
