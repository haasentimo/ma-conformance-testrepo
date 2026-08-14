"""Bounded in-memory cache behind the adapter facade.

Used for the small, hot lookups of the depot — tariff zones, depot codes,
label templates — where a round trip to the database costs more than the
memory. Insertion order of a dict carries the recency, so no extra bookkeeping
is needed.
"""


class LruCache:
    """Least-recently-used cache with a fixed number of slots."""

    def __init__(self, capacity: int = 256) -> None:
        if capacity < 1:
            raise ValueError("capacity must be at least one slot")
        self.capacity: int = capacity
        self.hits: int = 0
        self.misses: int = 0
        self._entries: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        """Return the cached value and mark it as the most recently used."""
        if key not in self._entries:
            self.misses += 1
            return None
        value = self._entries.pop(key)
        self._entries[key] = value
        self.hits += 1
        return value

    def put(self, key: str, value: str) -> None:
        """Store a value, evicting the least recently used entry when full."""
        if key in self._entries:
            self._entries.pop(key)
        elif len(self._entries) >= self.capacity:
            self._entries.pop(next(iter(self._entries)))
        self._entries[key] = value

    def invalidate(self, key: str) -> None:
        """Drop a single entry; an unknown key is ignored."""
        self._entries.pop(key, None)

    def clear(self) -> None:
        """Drop every entry and reset the counters."""
        self._entries.clear()
        self.hits = 0
        self.misses = 0

    def size(self) -> int:
        """Report how many slots are currently taken."""
        return len(self._entries)
