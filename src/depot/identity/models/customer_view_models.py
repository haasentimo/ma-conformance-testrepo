"""Read models behind the counter overview screen.

The clerk at the counter needs one flat row per customer — name, how much is
waiting on the shelf, when they were last here. No single table holds that, and
joining it per keystroke was too slow on the depot's hardware, so a nightly job
writes these rows and the screen reads them straight. They are never written
through from the counter.
"""

import sqlalchemy.orm

import depot.core.errors

SHELF_SLOTS_PER_CUSTOMER: int = 8


class CustomerSummary:
    """One row of the counter overview, refreshed by the nightly job."""

    __tablename__ = "customer_summary"

    customer_id: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        primary_key=True
    )
    reference: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(unique=True)
    display_name: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column()
    awaiting_collection: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        default=0
    )
    handed_in_today: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(default=0)
    last_visit: sqlalchemy.orm.Mapped[float | None] = sqlalchemy.orm.mapped_column(
        default=None
    )

    def shelf_pressure(self) -> float:
        """Report how full the customer's shelf slot is, from 0.0 to 1.0."""
        if self.awaiting_collection <= 0:
            return 0.0
        return min(1.0, self.awaiting_collection / SHELF_SLOTS_PER_CUSTOMER)

    def is_overflowing(self) -> bool:
        """Report whether the parcels no longer fit the customer's slot."""
        return self.awaiting_collection > SHELF_SLOTS_PER_CUSTOMER

    def needs_reminder(self, now_epoch: float, grace_seconds: float) -> bool:
        """Report whether the customer should be reminded to collect."""
        if grace_seconds <= 0:
            raise depot.core.errors.ValidationError(
                "grace_seconds", "must be a positive number of seconds"
            )
        if self.awaiting_collection <= 0 or self.last_visit is None:
            return False
        return now_epoch - self.last_visit > grace_seconds

    def headline(self) -> str:
        """Build the single line the overview shows for this customer."""
        return f"{self.display_name} — {self.awaiting_collection} waiting"
