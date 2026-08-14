"""Read models behind the packing list and the shelf labels.

What the packer carries through the hall is a sheet per order: one row per
parcel, with the shelf slot, the handling marks and a check digit that the
scanner compares against the barcode. The rows are built once when an order is
released to the hall and are not touched again — a packer walking the aisles
must see exactly what was printed, even if the order changes behind them.
"""

import sqlalchemy.orm

import depot.core.errors

HANDLING_FRAGILE: str = "fragile"
HANDLING_HEAVY: str = "heavy"


class PackingListRow:
    """One printed row of a packing list."""

    __tablename__ = "packing_list_row"

    line_id: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(primary_key=True)
    reference: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(unique=True)
    order_reference: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column()
    description: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column()
    shelf_slot: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column()
    handling: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(default="")
    printed_at: sqlalchemy.orm.Mapped[float | None] = sqlalchemy.orm.mapped_column(
        default=None
    )

    def marks(self) -> list[str]:
        """List the handling marks printed next to the description."""
        return [mark for mark in self.handling.split(",") if mark]

    def is_fragile(self) -> bool:
        """Report whether the packer has to reach for the padded sleeve."""
        return HANDLING_FRAGILE in self.marks()

    def check_digit(self) -> int:
        """Compute the digit the scanner compares against the barcode."""
        if not self.reference:
            raise depot.core.errors.ValidationError(
                "reference", "a printed row without a reference cannot be scanned"
            )
        return sum(ord(character) for character in self.reference) % 10

    def barcode(self) -> str:
        """Build the string the barcode on this row encodes."""
        return f"{self.reference}-{self.check_digit()}"
