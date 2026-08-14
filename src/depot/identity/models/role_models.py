"""Roles a depot staff account can hold.

The three roles are ordered: a dispatcher may do everything a counter clerk
may, a depot manager everything a dispatcher may. Nothing outside this module
relies on that order except the comparison below.
"""

import depot.core.errors

COUNTER_CLERK: str = "counter_clerk"
DISPATCHER: str = "dispatcher"
DEPOT_MANAGER: str = "depot_manager"

ROLE_ORDER: tuple[str, ...] = (COUNTER_CLERK, DISPATCHER, DEPOT_MANAGER)

ACCEPT_PARCEL: str = "parcel.accept"
RELEASE_PARCEL: str = "parcel.release"
OVERRIDE_HOLD: str = "parcel.override_hold"
CLOSE_DEPOT_DAY: str = "depot.close_day"


class Role:
    """A named role together with the permissions it grants."""

    def __init__(self, name: str, permissions: frozenset[str]) -> None:
        if name not in ROLE_ORDER:
            raise depot.core.errors.ValidationError("name", f"unknown role {name!r}")
        self.name: str = name
        self.permissions: frozenset[str] = permissions

    def grants(self, permission: str) -> bool:
        """Report whether this role carries the permission."""
        return permission in self.permissions

    def outranks(self, other: "Role") -> bool:
        """Report whether this role sits above another in the depot hierarchy."""
        return ROLE_ORDER.index(self.name) > ROLE_ORDER.index(other.name)

    def require(self, permission: str) -> None:
        """Raise unless this role carries the permission."""
        if not self.grants(permission):
            raise depot.core.errors.PermissionDeniedError(
                f"role {self.name!r} may not {permission}"
            )


def counter_clerk() -> Role:
    """Build the role every new counter account starts with."""
    return Role(COUNTER_CLERK, frozenset({ACCEPT_PARCEL, RELEASE_PARCEL}))


def dispatcher() -> Role:
    """Build the role that may also lift a hold on a parcel."""
    return Role(DISPATCHER, frozenset({ACCEPT_PARCEL, RELEASE_PARCEL, OVERRIDE_HOLD}))


def depot_manager() -> Role:
    """Build the role that may close the depot day."""
    return Role(
        DEPOT_MANAGER,
        frozenset({ACCEPT_PARCEL, RELEASE_PARCEL, OVERRIDE_HOLD, CLOSE_DEPOT_DAY}),
    )
