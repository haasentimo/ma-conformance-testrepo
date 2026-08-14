"""Read models behind the monthly account statement.

Business customers get one sheet a month listing every open item with its age,
and the depot's own bookkeeping reads the same rows to age the receivables into
buckets. Both want the figures as they stood at the close of the month, so the
rows are written once by the closing run and never corrected afterwards — a
statement that changes after it was sent is worse than one that is stale.
"""

import sqlalchemy.orm

import depot.core.errors

BUCKET_EDGES_DAYS: tuple[int, ...] = (30, 60, 90)
BUCKET_NAMES: tuple[str, ...] = ("current", "30d", "60d", "90d+")


class DebtorStatementLine:
    """One open item on the monthly statement of a debtor."""

    __tablename__ = "debtor_statement_line"

    line_id: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(primary_key=True)
    statement_month: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column()
    customer_reference: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column()
    document_number: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column()
    open_cents: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(default=0)
    age_days: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(default=0)
    disputed: sqlalchemy.orm.Mapped[bool] = sqlalchemy.orm.mapped_column(default=False)

    def bucket(self) -> str:
        """Report which ageing bucket this item falls into."""
        for index, edge in enumerate(BUCKET_EDGES_DAYS):
            if self.age_days <= edge:
                return BUCKET_NAMES[index]
        return BUCKET_NAMES[-1]

    def counts_towards_dunning(self) -> bool:
        """Report whether the dunning run may take this item into account."""
        return self.open_cents > 0 and not self.disputed

    def printed_amount(self) -> str:
        """Format the open amount the way the statement prints it."""
        if not self.statement_month:
            raise depot.core.errors.ValidationError(
                "statement_month", "a statement line needs the month it belongs to"
            )
        return f"{self.open_cents // 100},{self.open_cents % 100:02d}"

    def headline(self) -> str:
        """Build the single line the statement shows for this item."""
        return f"{self.document_number}  {self.printed_amount()}  {self.bucket()}"
