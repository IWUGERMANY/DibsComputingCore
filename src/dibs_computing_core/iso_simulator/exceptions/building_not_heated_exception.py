from .base import DIBSConfigurationError


class BuildingNotHeatedError(DIBSConfigurationError):
    """Raised when a building cannot be simulated as heated."""

    code = "DIBS_BUILDING_NOT_HEATED"
