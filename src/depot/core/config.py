"""Runtime configuration of a single depot site."""

DEFAULT_CURRENCY: str = "EUR"
DEFAULT_SESSION_TTL_SECONDS: int = 3600
MAX_PARCEL_WEIGHT_GRAMS: int = 31500
MAX_PARCEL_GIRTH_CM: int = 300


class DepotSettings:
    """The settings every context reads once at start-up.

    The weight and girth limits are the ones printed on the acceptance counter
    notice; carriers reject anything above them, so the depot refuses it first.
    """

    def __init__(
        self,
        database_url: str,
        depot_code: str,
        currency: str = DEFAULT_CURRENCY,
        session_ttl_seconds: int = DEFAULT_SESSION_TTL_SECONDS,
        max_parcel_weight_grams: int = MAX_PARCEL_WEIGHT_GRAMS,
        max_parcel_girth_cm: int = MAX_PARCEL_GIRTH_CM,
    ) -> None:
        self.database_url: str = database_url
        self.depot_code: str = depot_code
        self.currency: str = currency
        self.session_ttl_seconds: int = session_ttl_seconds
        self.max_parcel_weight_grams: int = max_parcel_weight_grams
        self.max_parcel_girth_cm: int = max_parcel_girth_cm

    def accepts_weight(self, weight_grams: int) -> bool:
        """Report whether a parcel of that weight may be handed in."""
        return 0 < weight_grams <= self.max_parcel_weight_grams

    def accepts_girth(self, length_cm: int, width_cm: int, height_cm: int) -> bool:
        """Report whether length plus twice width plus twice height still fits."""
        girth = length_cm + 2 * width_cm + 2 * height_cm
        return 0 < girth <= self.max_parcel_girth_cm
