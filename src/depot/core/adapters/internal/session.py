"""Database sessions behind the adapter facade.

A session collects the statements of one unit of work and writes them at the
commit. Nothing here is thread-safe; a session belongs to one request.
"""


class Session:
    """A single unit of work against the depot database."""

    def __init__(self, connection_string: str) -> None:
        self.connection_string: str = connection_string
        self.closed: bool = False
        self._pending: list[str] = []

    def execute(self, statement: str) -> None:
        """Queue a statement for the next commit."""
        if self.closed:
            raise RuntimeError("session is closed")
        self._pending.append(statement)

    def commit(self) -> int:
        """Write the queued statements and report how many were written."""
        if self.closed:
            raise RuntimeError("session is closed")
        written = len(self._pending)
        self._pending.clear()
        return written

    def rollback(self) -> None:
        """Discard everything queued since the last commit."""
        self._pending.clear()

    def close(self) -> None:
        """Release the session; anything still queued is lost."""
        self._pending.clear()
        self.closed = True

    def pending(self) -> int:
        """Report how many statements wait for the next commit."""
        return len(self._pending)


class SessionFactory:
    """Hands out sessions for one configured database."""

    def __init__(self, connection_string: str) -> None:
        self.connection_string: str = connection_string
        self.opened: int = 0

    def open(self) -> Session:
        """Open a fresh session and count it."""
        self.opened += 1
        return Session(self.connection_string)
