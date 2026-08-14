"""Use cases of the orders context.

The pricing sub-package is wired here rather than in each service, so that the
whole context quotes with one and the same handling percentage. Everything the
services need from it goes through the two functions below.
"""

import depot.orders.services.pricing.engine

HANDLING_PERCENT: int = 12


def quote_parcel_cents(weight_grams: int, fragile: bool, two_hands: bool) -> int:
    """Quote one parcel with the settings this context prices on."""
    engine = depot.orders.services.pricing.engine.PricingEngine(HANDLING_PERCENT)
    return engine.quote_cents(weight_grams, fragile, two_hands)


def weight_band(weight_grams: int) -> int:
    """Report the weight band a parcel falls into, counting from zero."""
    engine = depot.orders.services.pricing.engine.PricingEngine(HANDLING_PERCENT)
    return engine.band_of(weight_grams)
