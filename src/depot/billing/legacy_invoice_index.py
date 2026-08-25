"""Index of the invoice numbers the depot's previous billing software issued.

Kept for the length of the archiving obligation: customers still query invoices
raised before the switch, and the numbering scheme changed with it. The index
is read from the archive export once and never written to again.
"""

LEGACY_NUMBER_PREFIX: str = "R"
LEGACY_NUMBER_LENGTH: int = 9


class LegacyInvoiceIndex:
    """Resolves a pre-migration invoice number to the number it became."""

    def __init__(self) -> None:
        self._numbers: dict[str, str] = {}

    def load_line(self, line: str) -> bool:
        """Take one line of the archive export and report whether it was usable.

        A line is ``<old number>;<new number>``. The export padded its columns,
        so both halves are stripped before they are filed.
        """
        old_number, separator, number = line.partition(";")
        if not separator:
            return False
        old_number = old_number.strip()
        number = number.strip()
        if not self.looks_legacy(old_number) or not number:
            return False
        self._numbers[old_number] = number
        return True

    def looks_legacy(self, old_number: str) -> bool:
        """Report whether a string has the shape of an old invoice number."""
        return (
            old_number.startswith(LEGACY_NUMBER_PREFIX)
            and len(old_number) == LEGACY_NUMBER_LENGTH
            and old_number[1:].isdigit()
        )

    def resolve(self, old_number: str) -> str | None:
        """Return the number an old one became, or None if unknown."""
        return self._numbers.get(old_number.strip())

    def size(self) -> int:
        """Report how many old numbers the index holds."""
        return len(self._numbers)
