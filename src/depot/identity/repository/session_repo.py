"""Counter sessions of the depot staff.

A session is opened when a clerk signs on at a counter terminal and carries the
role the terminal was signed on with. Expiry is kept as an absolute epoch so
that the repository needs no time source of its own; whoever extends a session
passes the seconds it should gain.
"""

import depot.core.ports
import depot.identity.models.role_models


class SessionRepository(depot.core.ports.SessionStore):
    """Keeps the counter sessions and the role each was opened with."""

    def __init__(self) -> None:
        self._expires_at: dict[str, float] = {}
        self._roles: dict[str, depot.identity.models.role_models.Role] = {}

    def open(
        self,
        session_id: str,
        role: depot.identity.models.role_models.Role,
        expires_at: float,
    ) -> None:
        """Sign a clerk on at a terminal until the given epoch."""
        self._expires_at[session_id] = expires_at
        self._roles[session_id] = role

    def touch(self, session_id: str, ttl_seconds: int) -> bool:
        """Extend a session and report whether it was still open."""
        if session_id not in self._expires_at:
            return False
        self._expires_at[session_id] += float(ttl_seconds)
        return True

    def revoke(self, session_id: str) -> None:
        """Sign the terminal off; an unknown session is ignored."""
        self._expires_at.pop(session_id, None)
        self._roles.pop(session_id, None)

    def role_of(
        self, session_id: str
    ) -> depot.identity.models.role_models.Role | None:
        """Return the role a session was opened with, or None."""
        return self._roles.get(session_id)

    def expires_at(self, session_id: str) -> float | None:
        """Return the epoch a session runs out at, or None."""
        return self._expires_at.get(session_id)

    def drop_expired(self, now_epoch: float) -> int:
        """Revoke every session that has run out and report how many."""
        stale = [
            session_id
            for session_id, expiry in self._expires_at.items()
            if expiry <= now_epoch
        ]
        for session_id in stale:
            self.revoke(session_id)
        return len(stale)
