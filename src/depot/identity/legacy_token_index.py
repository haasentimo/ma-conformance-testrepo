"""Index of the tokens issued by the depot's previous counter software.

Kept for the length of the migration window: collection slips printed before
the switch carry these tokens instead of a customer reference, and the counter
has to resolve them until the last of those parcels has left the shelf. Nothing
writes here any more; the index is loaded once from the export file.
"""

TOKEN_LENGTH: int = 12


class LegacyTokenIndex:
    """Resolves a pre-migration token to the account number it belonged to."""

    def __init__(self) -> None:
        self._accounts: dict[str, str] = {}

    def load_line(self, line: str) -> bool:
        """Take one line of the export file and report whether it was usable.

        A line is ``<token>;<account number>``. The export was written by a
        system that padded short tokens with spaces, so both halves are
        stripped before they are filed.
        """
        token, separator, account_number = line.partition(";")
        if not separator:
            return False
        token = token.strip()
        account_number = account_number.strip()
        if len(token) != TOKEN_LENGTH or not account_number:
            return False
        self._accounts[token] = account_number
        return True

    def resolve(self, token: str) -> str | None:
        """Return the account number behind a token, or None if unknown."""
        return self._accounts.get(token.strip())

    def knows(self, token: str) -> bool:
        """Report whether a token appears in the index at all."""
        return token.strip() in self._accounts

    def size(self) -> int:
        """Report how many tokens the index holds."""
        return len(self._accounts)
