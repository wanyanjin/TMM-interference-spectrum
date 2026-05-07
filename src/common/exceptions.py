"""Project-level exception hierarchy."""


class TMMInterferenceError(Exception):
    """Base exception for project-level errors."""


class DataModelError(TMMInterferenceError):
    """Raised when domain data models are invalid."""


class ReaderNotFoundError(TMMInterferenceError):
    """Raised when no reader can handle a data source."""
