from .base import DIBSDataSourceError


class UsageTimeError(DIBSDataSourceError):
    """Raised when usage times cannot be resolved."""

    code = "DIBS_USAGE_TIME_NOT_FOUND"
