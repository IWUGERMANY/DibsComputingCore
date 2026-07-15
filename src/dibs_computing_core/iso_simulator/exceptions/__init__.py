"""Public exception contract of the DIBS computing core."""

from .base import (
    DIBSConfigurationError,
    DIBSDataSourceError,
    DIBSError,
    DIBSInputError,
    DIBSResultError,
    DIBSSimulationError,
    SimulationStateError,
    ThermalCalculationError,
    UnsupportedSystemError,
)
from .building_not_heated_exception import BuildingNotHeatedError
from .ghg_emission import GHGEmissionError
from .plz_exception import PLZNotFoundError
from .uk_or_hk_exception import HkOrUkNotFoundError
from .usage_time_exception import UsageTimeError

__all__ = [
    "BuildingNotHeatedError",
    "DIBSConfigurationError",
    "DIBSDataSourceError",
    "DIBSError",
    "DIBSInputError",
    "DIBSResultError",
    "DIBSSimulationError",
    "GHGEmissionError",
    "HkOrUkNotFoundError",
    "PLZNotFoundError",
    "SimulationStateError",
    "ThermalCalculationError",
    "UnsupportedSystemError",
    "UsageTimeError",
]