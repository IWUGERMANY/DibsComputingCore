from .base import DIBSResultError


class GHGEmissionError(DIBSResultError):
    """Raised when GHG emissions cannot be calculated."""

    code = "DIBS_GHG_CALCULATION_FAILED"
