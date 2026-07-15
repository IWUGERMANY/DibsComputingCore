from .base import DIBSDataSourceError


class PLZNotFoundError(DIBSDataSourceError):
    """Raised when a postcode cannot be resolved."""

    code = "DIBS_POSTCODE_NOT_FOUND"
