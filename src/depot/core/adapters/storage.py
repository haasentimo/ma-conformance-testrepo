"""Public storage adapter.

This is the surface the context services depend on. It keeps the documents
that belong to a parcel — the shipping label, the customs form, the handover
manifest — and it is deliberately free of any database session: the facade
owns those.
"""

import depot.core.ports


class ParcelDocumentStore:
    """Stores the documents that belong to a parcel, keyed by tracking code."""

    def __init__(self, bucket: str, clock: depot.core.ports.Clock) -> None:
        self.bucket: str = bucket
        self.clock: depot.core.ports.Clock = clock
        self._documents: dict[str, bytes] = {}

    def put_label(self, tracking_code: str, label: bytes) -> str:
        """Store a shipping label and return the key it was written under."""
        key = self.key_for(tracking_code, "label")
        self._documents[key] = label
        return key

    def put_manifest(self, tracking_code: str, manifest: bytes) -> str:
        """Store a handover manifest and return the key it was written under."""
        key = self.key_for(tracking_code, "manifest")
        self._documents[key] = manifest
        return key

    def key_for(self, tracking_code: str, kind: str) -> str:
        """Build the storage key of a document handed in today."""
        return f"{self.bucket}/{self.clock.today_iso()}/{tracking_code}.{kind}"

    def read(self, key: str) -> bytes | None:
        """Return a stored document, or None if the key is unknown."""
        return self._documents.get(key)

    def drop(self, key: str) -> bool:
        """Delete a document and report whether it had been there."""
        return self._documents.pop(key, None) is not None
