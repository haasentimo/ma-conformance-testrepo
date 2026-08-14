"""Price calculation for a shipment.

What the carrier charges is one thing; what the depot charges is that plus the
handling it does itself. This module owns the second part: the weight bands,
the surcharges the counter can see on the quote, and the rounding rule. It
deliberately knows nothing about orders, storage or carriers.
"""

import depot.core.errors

BAND_EDGES_GRAMS: tuple[int, ...] = (2000, 5000, 10000, 20000, 31500)
BAND_PRICES_CENTS: tuple[int, ...] = (490, 690, 990, 1490, 1990)

FRAGILE_SURCHARGE_CENTS: int = 250
TWO_HAND_SURCHARGE_CENTS: int = 400
ROUNDING_STEP_CENTS: int = 10


class PricingEngine:
    """Turns weight and handling into the price the counter quotes."""

    def __init__(self, handling_percent: int = 0) -> None:
        if not 0 <= handling_percent <= 100:
            raise depot.core.errors.ValidationError(
                "handling_percent", "must be between 0 and 100"
            )
        self.handling_percent: int = handling_percent

    def band_of(self, weight_grams: int) -> int:
        """Report which weight band a parcel falls into, counting from zero."""
        if weight_grams <= 0:
            raise depot.core.errors.ValidationError(
                "weight_grams", "a parcel has to weigh something"
            )
        for index, edge in enumerate(BAND_EDGES_GRAMS):
            if weight_grams <= edge:
                return index
        raise depot.core.errors.ValidationError(
            "weight_grams", f"above the {BAND_EDGES_GRAMS[-1]} g the depot accepts"
        )

    def base_cents(self, weight_grams: int) -> int:
        """Report the price of the band a parcel falls into."""
        return BAND_PRICES_CENTS[self.band_of(weight_grams)]

    def quote_cents(self, weight_grams: int, fragile: bool, two_hands: bool) -> int:
        """Quote one parcel, surcharges and handling included."""
        total = self.base_cents(weight_grams)
        if fragile:
            total += FRAGILE_SURCHARGE_CENTS
        if two_hands:
            total += TWO_HAND_SURCHARGE_CENTS
        total += total * self.handling_percent // 100
        return self.round_up(total)

    def round_up(self, amount_cents: int) -> int:
        """Round a price up to the step the price list is printed in."""
        remainder = amount_cents % ROUNDING_STEP_CENTS
        if remainder == 0:
            return amount_cents
        return amount_cents + ROUNDING_STEP_CENTS - remainder
