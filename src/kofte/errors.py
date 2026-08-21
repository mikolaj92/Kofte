"""Public errors. Hosts can catch these without importing internals."""


class KofteError(Exception):
    """Base error for the library."""


class UnknownProfileError(KofteError, KeyError):
    """Style id is not in the registry."""

    def __init__(self, profile_id: str) -> None:
        self.profile_id = profile_id
        super().__init__(f"unknown profile {profile_id!r}")


class FilterError(KofteError):
    """A filter rejected or failed a translation."""

    def __init__(self, message: str, filter_name: str | None = None) -> None:
        self.filter_name = filter_name
        prefix = f"{filter_name}: " if filter_name else ""
        super().__init__(prefix + message)


class LLMNotConfiguredError(KofteError, RuntimeError):
    """An LLM client is required and none was supplied."""
