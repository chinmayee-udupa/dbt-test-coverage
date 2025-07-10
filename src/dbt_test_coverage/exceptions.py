class DbtTestCoverageError(Exception):
    """Base exception for all package errors."""

    pass


class ManifestNotFoundError(DbtTestCoverageError):
    """Raised when the manifest file cannot be found."""

    pass


class InvalidManifestError(DbtTestCoverageError):
    """Raised when the manifest file is invalid."""

    pass
