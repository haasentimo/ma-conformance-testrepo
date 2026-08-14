"""Invoices the depot issues for the shipments it has carried out.

An invoice is raised when an order leaves the depot and is settled when the
money has arrived in full. Partial payments are normal with business customers,
so the open amount is kept on the invoice rather than worked out from the
payments every time the dunning run asks.
"""

import sqlalchemy.orm

import depot.core.errors

STATUS_DRAFT: str = "draft"
STATUS_ISSUED: str = "issued"
STATUS_SETTLED: str = "settled"
STATUS_WRITTEN_OFF: str = "written_off"

DEFAULT_TERMS_DAYS: int = 30
VAT_PERCENT: int = 19


class Invoice:
    """One invoice and everything the billing run decided about it."""

    __tablename__ = "invoice"

    id: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(primary_key=True)
    number: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(unique=True)
    customer_reference: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column()
    order_reference: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column()
    status: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        default=STATUS_DRAFT
    )
    net_cents: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(default=0)
    settled_cents: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(default=0)
    issued_at: sqlalchemy.orm.Mapped[float | None] = sqlalchemy.orm.mapped_column(
        default=None
    )
    terms_days: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        default=DEFAULT_TERMS_DAYS
    )
    reminders_sent: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(default=0)

    def vat_cents(self) -> int:
        """Report the tax on top of the net amount, rounded down."""
        return self.net_cents * VAT_PERCENT // 100

    def gross_cents(self) -> int:
        """Report what the customer owes in total."""
        return self.net_cents + self.vat_cents()

    def open_cents(self) -> int:
        """Report what is still outstanding on this invoice."""
        return max(0, self.gross_cents() - self.settled_cents)

    def issue(self, issued_at: float) -> None:
        """Raise the invoice and start the payment term running."""
        if self.status != STATUS_DRAFT:
            raise depot.core.errors.ConflictError(
                f"an invoice in {self.status!r} cannot be issued again"
            )
        if self.net_cents <= 0:
            raise depot.core.errors.ValidationError(
                "net_cents", "an invoice without an amount cannot be issued"
            )
        self.status = STATUS_ISSUED
        self.issued_at = issued_at

    def settle(self, amount_cents: int) -> int:
        """Book money against the invoice and report what stays open."""
        if amount_cents <= 0:
            raise depot.core.errors.ValidationError(
                "amount_cents", "a settlement has to move money"
            )
        self.settled_cents += amount_cents
        if self.open_cents() == 0:
            self.status = STATUS_SETTLED
        return self.open_cents()

    def due_at(self) -> float | None:
        """Report when the invoice falls due, or None while it is a draft."""
        if self.issued_at is None:
            return None
        return self.issued_at + self.terms_days * 86400.0

    def is_overdue(self, now_epoch: float) -> bool:
        """Report whether the payment term has run out with money still open."""
        due = self.due_at()
        return due is not None and now_epoch > due and self.open_cents() > 0
