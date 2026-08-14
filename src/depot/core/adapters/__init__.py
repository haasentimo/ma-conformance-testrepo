"""Adapter facade.

The only module that reaches into ``depot.core.adapters.internal``. Context
services take the session, the cache and the port protocols from here; the
public storage adapter next door they import directly.

The re-exports resolve lazily. Depot code imports whole modules
(``import depot.x.y``) and never single names, so a name of a sub-package
cannot be read while this package is still executing — at that moment
``depot.core`` does not carry the ``adapters`` attribute yet. Resolving on
first attribute access sidesteps that without giving up the import style.
"""

import depot.core.adapters.internal.cache
import depot.core.adapters.internal.session
import depot.core.ports

__all__ = [
    "DocumentStore",
    "LruCache",
    "Session",
    "SessionFactory",
    "SessionStore",
]


def __getattr__(name: str) -> object:
    """Resolve a re-exported name against the module it really lives in."""
    if name in ("DocumentStore", "SessionStore"):
        return getattr(depot.core.ports, name)
    if name in ("Session", "SessionFactory"):
        return getattr(depot.core.adapters.internal.session, name)
    if name == "LruCache":
        return depot.core.adapters.internal.cache.LruCache
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
