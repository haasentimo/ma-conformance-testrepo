"""Request and response shapes of the identity endpoints.

The schemas validate what a client sent before anything below the API sees it,
so that a malformed body never reaches a service. They know nothing about the
records themselves — that translation is the mappers' job.
"""

import depot.core.errors

MIN_PHONE_DIGITS: int = 6


class CustomerRegistration:
    """Body of a customer registration request."""

    def __init__(self, email: str, display_name: str, phone: str) -> None:
        self.email: str = email
        self.display_name: str = display_name
        self.phone: str = phone

    def validate(self) -> None:
        """Raise unless the body can be turned into a customer."""
        if "@" not in self.email:
            raise depot.core.errors.ValidationError("email", "must contain '@'")
        if not self.display_name.strip():
            raise depot.core.errors.ValidationError(
                "display_name", "must not be blank"
            )
        digits = [character for character in self.phone if character.isdigit()]
        if len(digits) < MIN_PHONE_DIGITS:
            raise depot.core.errors.ValidationError(
                "phone", f"needs at least {MIN_PHONE_DIGITS} digits"
            )


class ContactChange:
    """Body of a request that changes the contact details of a customer."""

    def __init__(self, fields: dict[str, str]) -> None:
        self.fields: dict[str, str] = fields

    def validate(self) -> None:
        """Raise unless at least one field was sent and none of them is blank."""
        if not self.fields:
            raise depot.core.errors.ValidationError(
                "fields", "a change request must carry at least one field"
            )
        for name, value in sorted(self.fields.items()):
            if not value.strip():
                raise depot.core.errors.ValidationError(name, "must not be blank")


class SignOn:
    """Body of a request that signs a clerk on at a counter terminal."""

    def __init__(self, terminal: str, role_name: str) -> None:
        self.terminal: str = terminal
        self.role_name: str = role_name

    def validate(self) -> None:
        """Raise unless the terminal and the role were both named."""
        if not self.terminal.strip():
            raise depot.core.errors.ValidationError("terminal", "must be named")
        if not self.role_name.strip():
            raise depot.core.errors.ValidationError("role_name", "must be named")


def error_body(error: depot.core.errors.DepotError) -> dict[str, str]:
    """Build the body the API returns for an error the depot raised."""
    return {"error": type(error).__name__, "message": error.message}
