"""Discount codes the depot honours on shipment orders.

A code is worth a percentage, never a fixed sum: the depot settles with the
carrier on the list price and keeps the difference, so a fixed discount on a
cheap zone could turn a shipment into a loss.
"""

import depot.core.errors

MAX_PERCENT: int = 40


class Discount:
    """A discount code together with the conditions it holds under."""

    def __init__(
        self,
        code: str,
        percent: int,
        min_subtotal_cents: int = 0,
        zones: frozenset[str] = frozenset(),
    ) -> None:
        if not code.strip():
            raise depot.core.errors.ValidationError("code", "must not be blank")
        if not 0 < percent <= MAX_PERCENT:
            raise depot.core.errors.ValidationError(
                "percent", f"must be between 1 and {MAX_PERCENT}"
            )
        self.code: str = code.strip().upper()
        self.percent: int = percent
        self.min_subtotal_cents: int = min_subtotal_cents
        self.zones: frozenset[str] = zones

    def applies_to(self, subtotal_cents: int, zone: str) -> bool:
        """Report whether this code may be used on that order."""
        if subtotal_cents < self.min_subtotal_cents:
            return False
        return not self.zones or zone in self.zones

    def cut_cents(self, subtotal_cents: int) -> int:
        """Report how much this code takes off a subtotal, rounded down."""
        return subtotal_cents * self.percent // 100


def house_codes() -> list[Discount]:
    """Build the codes the depot itself hands out at the counter."""
    return [
        Discount("REGULAR10", 10, min_subtotal_cents=2000),
        Discount("BULK25", 25, min_subtotal_cents=15000),
        Discount("NEARZONE15", 15, zones=frozenset({"DE-S", "DE-W"})),
    ]
