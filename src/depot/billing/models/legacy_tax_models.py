"""Tax rates the depot's previous billing software worked with.

Kept for the length of the archiving obligation: an invoice raised before the
switch has to be reproducible with the rate that applied on its date, and the
rates changed twice in that period. Nothing writes here any more — the table is
read from the archive export and left alone.
"""

RATE_SCALE: int = 100
ARCHIVE_UNTIL_YEAR: int = 2035


class LegacyTaxRate:
    """One tax rate together with the period it applied in."""

    def __init__(
        self, code: str, percent_scaled: int, valid_from: str, valid_to: str
    ) -> None:
        self.code: str = code
        self.percent_scaled: int = percent_scaled
        self.valid_from: str = valid_from
        self.valid_to: str = valid_to

    def applies_on(self, day: str) -> bool:
        """Report whether this rate was the one in force on a given day."""
        return self.valid_from <= day <= self.valid_to

    def tax_cents(self, net_cents: int) -> int:
        """Report the tax this rate puts on a net amount, rounded down."""
        return net_cents * self.percent_scaled // (100 * RATE_SCALE)


class LegacyTaxTable:
    """The whole rate table as the archive export delivered it."""

    def __init__(self) -> None:
        self._rates: list[LegacyTaxRate] = []

    def load_line(self, line: str) -> bool:
        """Take one line of the archive export and report whether it was usable.

        A line is ``<code>;<percent times 100>;<from>;<to>``, dates in ISO form.
        The export was written with fixed-width columns, so every field is
        stripped before it is filed.
        """
        fields = [field.strip() for field in line.split(";")]
        if len(fields) != 4:
            return False
        code, scaled, valid_from, valid_to = fields
        if not code or not scaled.isdigit() or not valid_from or not valid_to:
            return False
        self._rates.append(LegacyTaxRate(code, int(scaled), valid_from, valid_to))
        return True

    def rate_on(self, day: str) -> LegacyTaxRate | None:
        """Return the rate that was in force on a day, or None."""
        for rate in self._rates:
            if rate.applies_on(day):
                return rate
        return None

    def codes(self) -> list[str]:
        """List the rate codes the table holds, without repetition."""
        return sorted({rate.code for rate in self._rates})

    def size(self) -> int:
        """Report how many rate periods the table holds."""
        return len(self._rates)
