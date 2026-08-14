"""Translation between roles and the shapes the API exchanges."""

import depot.core.errors
import depot.identity.models.role_models

LABELS: dict[str, str] = {
    depot.identity.models.role_models.COUNTER_CLERK: "counter clerk",
    depot.identity.models.role_models.DISPATCHER: "dispatcher",
    depot.identity.models.role_models.DEPOT_MANAGER: "depot manager",
}


def to_payload(role: depot.identity.models.role_models.Role) -> dict[str, object]:
    """Build the body a role endpoint returns for one role."""
    return {
        "name": role.name,
        "label": LABELS.get(role.name, role.name),
        "permissions": sorted(role.permissions),
    }


def from_name(name: str) -> depot.identity.models.role_models.Role:
    """Build the role a request named, with the permissions it carries."""
    if name == depot.identity.models.role_models.COUNTER_CLERK:
        return depot.identity.models.role_models.counter_clerk()
    if name == depot.identity.models.role_models.DISPATCHER:
        return depot.identity.models.role_models.dispatcher()
    if name == depot.identity.models.role_models.DEPOT_MANAGER:
        return depot.identity.models.role_models.depot_manager()
    raise depot.core.errors.ValidationError("role", f"unknown role {name!r}")


def catalogue() -> list[dict[str, object]]:
    """Build the list of roles the terminal offers when signing on."""
    return [
        to_payload(depot.identity.models.role_models.counter_clerk()),
        to_payload(depot.identity.models.role_models.dispatcher()),
        to_payload(depot.identity.models.role_models.depot_manager()),
    ]
