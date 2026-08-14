"""Public storage adapter.

This is the surface the context services depend on. It keeps the documents that
belong to a parcel — the shipping label, the customs form, the handover
manifest — and it is deliberately free of any database session: the facade owns
those.

It is also free of a clock. The day a document is filed under comes in with the
document, because the shift that produced a manifest and the moment it reaches
the store are not the same thing.
"""

import depot.core.ports


class ParcelDocumentStore(depot.core.ports.DocumentStore):
    """Stores the documents that belong to a parcel, keyed by tracking code."""

    def __init__(self, bucket: str) -> None:
        self.bucket: str = bucket
        self._documents: dict[str, bytes] = {}

    def key_for(self, tracking_code: str, day: str, kind: str) -> str:
        """Build the storage key of a document filed for a given day."""
        return f"{self.bucket}/{day}/{tracking_code}.{kind}"

    def put_label(self, tracking_code: str, day: str, label: bytes) -> str:
        """Store a shipping label and return the key it was written under."""
        key = self.key_for(tracking_code, day, "label")
        self._documents[key] = label
        return key

    def put_manifest(self, tracking_code: str, day: str, manifest: bytes) -> str:
        """Store a handover manifest and return the key it was written under."""
        key = self.key_for(tracking_code, day, "manifest")
        self._documents[key] = manifest
        return key

    def read(self, key: str) -> bytes | None:
        """Return a stored document, or None if the key is unknown."""
        return self._documents.get(key)

    def drop(self, key: str) -> bool:
        """Delete a document and report whether it had been there."""
        return self._documents.pop(key, None) is not None

    def keys_of_day(self, day: str) -> list[str]:
        """List the keys filed for one day, in storage order."""
        prefix = f"{self.bucket}/{day}/"
        return sorted(key for key in self._documents if key.startswith(prefix))
