"""Bearer tokens for the counter terminals.

A terminal signs on once and then carries a token on every call. The token
itself is signed outside the depot — the service only decides whether a session
is still good for one and what subject the token should name.
"""

import depot.identity.repository.session_repo

DEFAULT_TTL_SECONDS: int = 900
SUBJECT_PREFIX: str = "counter"


class TokenService:
    """Issues and checks the tokens the counter terminals carry."""

    def __init__(
        self, sessions: depot.identity.repository.session_repo.SessionRepository
    ) -> None:
        self.sessions: depot.identity.repository.session_repo.SessionRepository = (
            sessions
        )

    def issue(self, session_id: str, signer: object) -> str:
        """Issue a token for a session that is still open.

        The session is extended by the same span the token is good for, so a
        terminal that keeps working never has to sign on twice.
        """
        if not self.sessions.touch(session_id, DEFAULT_TTL_SECONDS):
            return ""
        return signer.sign(self.subject_of(session_id), DEFAULT_TTL_SECONDS)

    def subject_of(self, session_id: str) -> str:
        """Build the subject a token for this session should name."""
        role = self.sessions.role_of(session_id)
        if role is None:
            return f"{SUBJECT_PREFIX}:unknown"
        return f"{SUBJECT_PREFIX}:{role.name}:{session_id}"

    def revoke(self, session_id: str) -> None:
        """Sign a terminal off, so the next call with its token fails."""
        self.sessions.revoke(session_id)

    def is_live(self, session_id: str, now_epoch: float) -> bool:
        """Report whether a session is still good at that moment."""
        expiry = self.sessions.expires_at(session_id)
        return expiry is not None and expiry > now_epoch
