"""Index of the order numbers the depot's previous counter software issued.

Kept for the length of the migration window: customers still call about
shipments booked before the switch, and the counter has to find them by the old
number. The index is loaded once from the export file and never written to
again.
"""

LEGACY_NUMBER_PREFIX: str = "A-"
LEGACY_NUMBER_LENGTH: int = 10


class LegacyOrderIndex:
    """Resolves a pre-migration order number to the reference it became."""

    def __init__(self) -> None:
        self._references: dict[str, str] = {}

    def load_line(self, line: str) -> bool:
        """Take one line of the export file and report whether it was usable.

        A line is ``<old number>;<new reference>``. The export was written by a
        system that padded its columns, so both halves are stripped first.
        """
        old_number, separator, reference = line.partition(";")
        if not separator:
            return False
        old_number = old_number.strip()
        reference = reference.strip()
        if not self.looks_legacy(old_number) or not reference:
            return False
        self._references[old_number] = reference
        return True

    def looks_legacy(self, old_number: str) -> bool:
        """Report whether a string has the shape of an old order number."""
        return (
            old_number.startswith(LEGACY_NUMBER_PREFIX)
            and len(old_number) == LEGACY_NUMBER_LENGTH
        )

    def resolve(self, old_number: str) -> str | None:
        """Return the reference an old number became, or None if unknown."""
        return self._references.get(old_number.strip())

    def size(self) -> int:
        """Report how many old numbers the index holds."""
        return len(self._references)
