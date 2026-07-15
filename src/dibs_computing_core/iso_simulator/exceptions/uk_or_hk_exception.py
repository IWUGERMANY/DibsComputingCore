from .base import DIBSDataSourceError


class HkOrUkNotFoundError(DIBSDataSourceError):
    """Raised when an HK/UK usage type cannot be resolved."""

    code = "DIBS_USAGE_TYPE_NOT_FOUND"
