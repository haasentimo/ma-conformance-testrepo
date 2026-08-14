"""Protocols the depot expects of its surroundings.

The core owns the interfaces, the adapters and the context services implement
them. Nothing here refers to a concrete technology, and nothing here imports
another depot module.
"""

import typing


class Clock(typing.Protocol):
    """Source of the current time.

    Injected rather than read from the wall clock so that bookings, expiry
    dates and dunning runs stay reproducible in a replay.
    """

    def now_epoch(self) -> float: ...

    def today_iso(self) -> str: ...


class TokenSigner(typing.Protocol):
    """Signs and verifies the opaque tokens handed to depot clients."""

    def sign(self, subject: str, ttl_seconds: int) -> str: ...

    def verify(self, token: str) -> str | None: ...


class SessionStore(typing.Protocol):
    """Keeps the counter sessions of the depot staff."""

    def touch(self, session_id: str, ttl_seconds: int) -> bool: ...

    def revoke(self, session_id: str) -> None: ...


class RateProvider(typing.Protocol):
    """Supplies the carrier rate for a destination zone and weight."""

    def rate_cents(self, zone: str, weight_grams: int) -> int: ...


class DiscountCatalog(typing.Protocol):
    """Answers which discount a code grants on a given subtotal."""

    def percent_for(self, code: str, subtotal_cents: int) -> int: ...


class PaymentGateway(typing.Protocol):
    """Moves money on behalf of the depot; the only outbound money path."""

    def refund(self, payment_reference: str, amount_cents: int) -> str: ...


class PaymentLedger(typing.Protocol):
    """Reports how much of an invoice has already been settled."""

    def settled_cents(self, invoice_number: str) -> int: ...
